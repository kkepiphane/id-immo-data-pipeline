from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp,
    trim, lower
)
from pyspark.sql.types import StructType, StringType

# =========================================================
# CONFIGURATION
# =========================================================
KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "immo_raw"

DATA_LAKE_PATH = "/opt/spark/data_lake"
RAW_PATH = f"{DATA_LAKE_PATH}/raw"
CHECKPOINT_RAW = f"{DATA_LAKE_PATH}/checkpoints/raw"

POSTGRES_URL = "jdbc:postgresql://postgres:5432/immo_db"
POSTGRES_TABLE = "proprietes"
POSTGRES_PROPS = {
    "user": "immo",
    "password": "immo12",
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
# SCHEMA (adapter selon Scrapy)
# =========================================================
schema = StructType() \
    .add("title", StringType()) \
    .add("url", StringType()) \
    .add("source", StringType())

# =========================================================
# LECTURE KAFKA
# =========================================================
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", TOPIC) \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .load()

# =========================================================
# PARSE JSON
# =========================================================
json_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# =========================================================
# NETTOYAGE DATA
# =========================================================
clean_df = json_df \
    .filter(col("title").isNotNull()) \
    .filter(col("url").isNotNull()) \
    .withColumn("title", trim(col("title"))) \
    .withColumn("title_clean", lower(trim(col("title")))) \
    .withColumn("source", trim(col("source"))) \
    .withColumn("scraped_at", current_timestamp())

# =========================================================
# DÉDUPLICATION
# =========================================================
dedup_df = clean_df.dropDuplicates(["url"])

# =========================================================
# 1. DATA LAKE (PARQUET OPTIMISÉ)
# =========================================================
raw_query = dedup_df.writeStream \
    .format("parquet") \
    .option("path", RAW_PATH) \
    .option("checkpointLocation", CHECKPOINT_RAW) \
    .outputMode("append") \
    .start()

# =========================================================
#  2. POSTGRES (ROBUSTE)
# =========================================================
def write_to_postgres(batch_df, batch_id):
    try:
        if batch_df.isEmpty():
            print(f"[Batch {batch_id}] Aucun enregistrement")
            return

        batch_df.write \
            .jdbc(
                url=POSTGRES_URL,
                table=POSTGRES_TABLE,
                mode="append",
                properties=POSTGRES_PROPS
            )

        print(f"[Batch {batch_id}] {batch_df.count()} lignes insérées")

    except Exception as e:
        print(f"[ERREUR][Batch {batch_id}] {e}")

postgres_query = dedup_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("append") \
    .start()

# =========================================================
# LANCEMENT
# =========================================================
spark.streams.awaitAnyTermination()