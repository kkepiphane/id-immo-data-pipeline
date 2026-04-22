from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp,
    trim, to_timestamp, coalesce, lit, regexp_replace, when
)
from pyspark.sql.types import StructType, StringType, LongType, ArrayType
import time
from kafka import KafkaAdminClient
from kafka.errors import NoBrokersAvailable

# =========================================================
# CONFIGURATION
# =========================================================
KAFKA_BOOTSTRAP = "kafka:9092"
TOPIC = "immo_raw"

DATA_LAKE_PATH = "hdfs://namenode:8020/data_lake"
RAW_PATH = f"{DATA_LAKE_PATH}/raw"
CHECKPOINT_RAW = "hdfs://namenode:8020/checkpoints/raw"
CHECKPOINT_PG = "hdfs://namenode:8020/checkpoints/postgres"

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
    .config("spark.local.dir", "/opt/spark/tmp") \
    .config("spark.sql.shuffle.partitions", "4") \
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

def wait_for_kafka_topic(bootstrap_server, topic, max_retries=30, delay=5):
    print(f"[INIT] Attente du topic '{topic}'...")
    for i in range(max_retries):
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=bootstrap_server,
                request_timeout_ms=5000
            )
            topics = admin.list_topics()
            admin.close()
            if topic in topics:
                print(f"[INIT] ✅ Topic '{topic}' prêt !")
                return
            print(f"[INIT] [{i+1}/{max_retries}] Topic absent, attente {delay}s...")
        except NoBrokersAvailable:
            print(f"[INIT] [{i+1}/{max_retries}] Kafka pas encore dispo, attente {delay}s...")
        except Exception as e:
            print(f"[INIT] [{i+1}/{max_retries}] Erreur: {e}, attente {delay}s...")
        time.sleep(delay)
    raise RuntimeError(f"Topic '{topic}' introuvable après {max_retries} tentatives.")

# Appel avant TOUT le reste
wait_for_kafka_topic(KAFKA_BOOTSTRAP, TOPIC)


# =========================================================
# LECTURE KAFKA
# =========================================================
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", TOPIC) \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false")\
    .option("maxOffsetsPerTrigger", 500)\
    .load()
    
query_debug = kafka_df.selectExpr("CAST(value AS STRING)") \
    .writeStream \
    .format("console") \
    .option("truncate", "false") \
    .outputMode("append") \
    .start()
# =========================================================
# PARSE ET NETTOYAGE
# =========================================================
parsed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# clean_df = parsed_df \
#     .filter(col("listing_id").isNotNull()) \
#     .withColumn("title", trim(col("title"))) \
#     .withColumn("price", col("price").cast("long")) \
#     .withColumn("processed_at", current_timestamp())\
#     .withColumn("bedrooms", regexp_replace(col("bedrooms"), "[^0-9]", "").cast("int")) \
#     .withColumn("square_footage", regexp_replace(col("square_footage"), "[^0-9]", "").cast("float")) \
#     .withColumn("wc_interne", regexp_replace(col("wc_interne"), "[^0-9]", "").cast("int")) \
#     .withColumn("bedrooms", when(col("bedrooms").isNull() | (col("bedrooms") > 15), lit(None)).otherwise(col("bedrooms")))

clean_df = parsed_df \
    .filter(col("listing_id").isNotNull()) \
    .withColumn("title", trim(col("title"))) \
    .withColumn("property_type",
        when(col("property_type").rlike("(?i)villa"), "Villa")
        .when(col("property_type").rlike("(?i)maison"), "Maison")
        .when(col("property_type").rlike("(?i)terrain"), "Terrain")
        .when(col("property_type").rlike("(?i)appartement"), "Appartement")
        .otherwise("Autre")
    ) \
    .withColumn("offer_type",
        when(col("offer_type").rlike("(?i)lou"), "Location")
        .when(col("offer_type").rlike("(?i)ven"), "Vente")
        .otherwise("Inconnu")
    ) \
    .withColumn("price", col("price").cast("long")) \
    .withColumn("bedrooms", col("bedrooms").cast("int")) \
    .withColumn("square_footage", col("square_footage").cast("float")) \
    .withColumn("wc_interne", col("wc_interne").cast("int")) \
    .filter(col("price").isNotNull()) \
    .filter(col("price") > 0) \
    .filter(col("city").isNotNull()) \
    .withColumn("processed_at", current_timestamp())


# dedup_df = clean_df.dropDuplicates(["listing_url"])
# clean_df.writeStream.format("console").start()

# =========================================================
# DESTINATION 1 : DATA LAKE (PARQUET)
# =========================================================
lake_query = clean_df.writeStream \
    .format("console") \
    .format("parquet") \
    .option("path", RAW_PATH) \
    .option("checkpointLocation", CHECKPOINT_RAW) \
    .outputMode("append") \
    .trigger(processingTime='30 seconds') \
    .start()
    
# =========================================================
# DESTINATION 2 : POSTGRES
# =========================================================
def write_to_postgres(batch_df, batch_id):
    try:
        # Mettre en cache pour éviter les recalculs
        batch_df.cache()
        count = batch_df.count()  # Une seule fois
        
        if count > 0:
            final_df = batch_df \
                .withColumn("image_urls", col("image_urls").cast("string"))
            # Déduplication ICI dans le batch
            final_df = final_df.dropDuplicates(["listing_url"])
            
            final_df.write.jdbc(
                url=POSTGRES_URL,
                table=POSTGRES_TABLE,
                mode="append",
                properties=POSTGRES_PROPS
            )
            print(f"--- [BATCH {batch_id}] {count} propriétés insérées.")
        
        batch_df.unpersist()
    except Exception as e:
        print(f"--- [ERREUR BATCH {batch_id}] : {e}")

postgres_query = clean_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .option("checkpointLocation", CHECKPOINT_PG) \
    .trigger(processingTime='30 seconds')\
    .start()

    
# =========================================================
# ATTENTE TERMINAISON
# =========================================================
spark.streams.awaitAnyTermination()
