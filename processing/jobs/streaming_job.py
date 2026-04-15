from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp,
    trim, lower, coalesce, lit
)
from pyspark.sql.types import StructType, StringType, LongType, ArrayType

# =========================================================
# CONFIGURATION
# =========================================================
KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "immo_raw"

DATA_LAKE_PATH = "/opt/spark/data_lake"
RAW_PATH = f"{DATA_LAKE_PATH}/raw"
CHECKPOINT_RAW = f"{DATA_LAKE_PATH}/checkpoints/raw"

POSTGRES_URL = "jdbc:postgresql://postgres-dw:5432/real_estate_dw"
POSTGRES_TABLE = "proprietes"
POSTGRES_PROPS = {
    "user": "dw_admin",
    "password": "dwpassword",
    "driver": "org.postgresql.Driver"
}

# =========================================================
# SPARK SESSION
# =========================================================
spark = SparkSession.builder \
    .appName("ImmoStreamingPipeline") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# =========================================================
# SCHEMA ALIGNÉ SUR PROPRIETEITEM
# =========================================================
schema = StructType() \
    .add("listing_id", StringType()) \
    .add("title", StringType()) \
    .add("property_type", StringType()) \
    .add("offer_type", StringType()) \
    .add("description", StringType()) \
    .add("bedrooms", StringType()) \
    .add("square_footage", StringType()) \
    .add("wc_interne", StringType()) \
    .add("legal_doc", StringType()) \
    .add("price", LongType()) \
    .add("address", StringType()) \
    .add("city", StringType()) \
    .add("neighborhood", StringType()) \
    .add("listing_url", StringType()) \
    .add("image_urls", ArrayType(StringType())) \
    .add("source", StringType()) \
    .add("scraped_at", StringType())

# =========================================================
# LECTURE KAFKA
# =========================================================
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

# =========================================================
# PARSE ET NETTOYAGE
# =========================================================
parsed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

clean_df = parsed_df \
    .filter(col("listing_id").isNotNull()) \
    .withColumn("title", trim(col("title"))) \
    .withColumn("price", coalesce(col("price"), lit(0))) \
    .withColumn("processed_at", current_timestamp())

# Déduplication sur l'URL pour éviter les doublons dans le même batch
dedup_df = clean_df.dropDuplicates(["listing_url"])

# =========================================================
# DESTINATION 1 : DATA LAKE (PARQUET)
# =========================================================
lake_query = dedup_df.writeStream \
    .format("parquet") \
    .option("path", RAW_PATH) \
    .option("checkpointLocation", CHECKPOINT_RAW) \
    .outputMode("append") \
    .start()

# =========================================================
# DESTINATION 2 : POSTGRES
# =========================================================
def write_to_postgres(batch_df, batch_id):
    try:
        if not batch_df.isEmpty():
            # On convertit la liste d'images en String pour Postgres (plus simple)
            final_df = batch_df.withColumn("image_urls", col("image_urls").cast("string"))
            
            final_df.write \
                .jdbc(
                    url=POSTGRES_URL,
                    table=POSTGRES_TABLE,
                    mode="append",
                    properties=POSTGRES_PROPS
                )
            print(f"--- [BATCH {batch_id}] {batch_df.count()} propriétés insérées.")
    except Exception as e:
        print(f"--- [ERREUR BATCH {batch_id}] : {e}")

postgres_query = dedup_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .start()

# =========================================================
# ATTENTE TERMINAISON
# =========================================================
spark.streams.awaitAnyTermination()
