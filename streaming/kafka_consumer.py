import json
import os
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime
from psycopg2.extras import execute_batch

# Configuration
KAFKA_SERVER = 'kafka:9092'
TOPIC_NAME = 'immo_raw'
RAW_PATH = '../data_lake/raw/'
DB_CONFIG = {
    "host": "immo_postgres",
    "database": "immo_db",
    "user": "immo",
    "password": "immo12"
}


def archive_to_datalake(items):
    """Sauvegarde un lot de données en JSON Lines compressé ou brut"""
    os.makedirs(RAW_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{RAW_PATH}batch_{timestamp}.jsonl"

    with open(filename, "a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"--- [ARCHIVAGE] {len(items)} items sauvegardés dans {filename}")


def insert_to_postgres(items):
    """Insère les annonces immobilières dans Postgres"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # On adapte la requête SQL avec les colonnes immo
        query = """
          INSERT INTO proprietes (listing_id, title, price, city, neighborhood, listing_url, scraped_at)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
          ON CONFLICT (listing_id) DO UPDATE SET price = EXCLUDED.price
          """
        
        data_to_insert = [
            (
                item.get('listing_id'), 
                item.get('title'), 
                item.get('price'), 
                item.get('city'), 
                item.get('neighborhood'), 
                item.get('listing_url'), 
                item.get('scraped_at')
            ) for item in items
        ]
        
        execute_batch(cur, query, data_to_insert)
        conn.commit()
        cur.close()
        conn.close()
        print(f"--- [POSTGRES] {len(items)} propriétés insérées/mises à jour")
    except Exception as e:
        print(f"Erreur Postgres: {e}")


# Initialisation du Consumer
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=[KAFKA_SERVER],
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='immo_archiver_group'
)

print("--- Consumer démarré. En attente de données...")

batch = []
BATCH_SIZE = 10  # On attend d'avoir 10 items avant d'écrire sur disque/DB

# for message in consumer:
#     item = message.value
#     batch.append(item)

#     if len(batch) >= BATCH_SIZE:
#         archive_to_datalake(batch)
#         insert_to_postgres(batch)
#         batch = []  # On vide le tampon