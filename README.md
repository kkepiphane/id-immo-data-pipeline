# Immo Data Engineering Pipeline

#GBADAMASSI ABDOU-AKIM

End-to-end data engineering pipeline for real estate data ingestion, processing, orchestration, and storage using modern Big Data tools.

## Architecture Overview

```
Scrapy → Kafka → Spark → Data Lake (HDFS)
                               ↓
                        Silver / Clean Data
                               ↓
                        PostgreSQL (DW)
```

## Tech Stack

| Tool | Purpose |
|------|---------|
| Scrapy | Data extraction |
| Apache Kafka | Streaming |
| Apache Spark | Processing and streaming |
| PostgreSQL | Data warehouse and metadata storage |
| Apache Airflow | Workflow orchestration |
| Docker Compose | Containerization |

## Project Structure

```
immo-data-pipeline/
├── ingestion/              # Scrapy spiders
├── kafka/  
├── processing/             # Spark jobs and Dockerfile
├── airflow/                # Airflow DAGs and configuration
├── warehouse/               # SQL scripts for data warehouse
├── data_lake/              # Parquet output from Spark
├── docker-compose.yml      # Infrastructure definition
└── README.md
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/kkepiphane/immo-data-pipeline.git
cd immo-data-pipeline
```

### 2. Start all services

```bash
docker compose up --build
```

### 3. Access services

| Service | URL |
|---------|-----|
| Airflow Webserver | http://localhost:8888 |
| Spark Master UI | http://localhost:8082 |
| Kafka Broker | localhost:9092 |
| PostgreSQL Data Warehouse | localhost:5434 |
| PostgreSQL Airflow Metadata | localhost:5433 |

### Airflow Credentials

- **Username:** `admin`
- **Password:** `admin`

## Pipeline Features

###  Data Ingestion
- Scrapy spiders for real estate websites
- Automated execution via Airflow
- Streaming output to Kafka

###  Streaming Layer
- Kafka topic: `immo_raw`
- Real-time data ingestion

### Processing Layer
- Spark Structured Streaming
- Data cleaning and transformation
- Deduplication of records
- Output to Data Lake (Parquet) + PostgreSQL

### Orchestration Layer
- Airflow DAGs for scheduling
- Daily pipeline execution

### Data Warehouse (PostgreSQL)
- Property listings
- Location data
- Pricing information
- Metadata from processed data

## DAG Structure

```
immo_scraping_pipeline
    ├── run_scrapers
    ├── send_to_kafka
    ├── spark_stream_processing
    └── load_to_postgres_dw
```

## Docker Services

| Service |
|---------|
| kafka |
| zookeeper |
| spark-master |
| spark-worker |
| postgres-dw |
| postgres-airflow |
| airflow-init |
| airflow-webserver |
| airflow-scheduler |

## Useful Commands

```bash
# Stop and clean everything
docker compose down -v

# Full restart
docker compose up --build -d

# Pour verifier les informations dans la base de donnes
docker exec -it immo-postgres-dw psql -U dw_admin -d real_estate_dw

#nombre total de ligne
SELECT count(*) FROM proprietes;

#Voir toutes les sources disponibles
SELECT DISTINCT source FROM proprietes;

# Supprimer le Checkpoint sur HDFS
docker exec namenode hdfs dfs -rm -r /checkpoints/raw

# Nettoyer les fichiers de données brutes (Data Lake)
docker exec namenode hdfs dfs -rm -r /data_lake/raw

# Réinitialiser la table Postgres
docker exec -it immo-postgres-dw psql -U dw_admin -d real_estate_dw -c "TRUNCATE TABLE proprietes;"
```

## Known Issues

- Airflow must finish initialization before login
- Kafka must be running before Scrapy execution
- Spark streaming requires active Kafka topic

## Future Improvements

- [ ] Add Prometheus + Grafana monitoring
- [ ] Replace BashOperator with DockerOperator
- [ ] Add Schema Registry for Kafka
- [ ] Integrate dbt for transformations
- [ ] Use S3/MinIO for scalable data lake storage

## License

MIT