from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime

default_args = {
    "owner": "Data engineer",
}

with DAG(
    dag_id="id_immo_scraping_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * 5",
    catchup=False,
    default_args=default_args,
    description="airflow → scraping → kafka → Spark →  Data Lake (HDFS) → Silver / Clean Data → PostgreSQL",
    tags=["airflow", "spark", "etl", "scrapy", "HDFS", "PostgreSQL", "id-immo"],
) as dag:

    spiders = ["intendance", "igoe", "coinafrique", "omnisoft"]
    # spiders = ["intendance", "igoe"]

    tasks = []

    for spider in spiders:
        task = DockerOperator(
            task_id=f"scrape_{spider}",
            image="immo_scraper:latest",
            command=f'bash -c "cd /app/ingestion && scrapy crawl {spider}"',
            network_mode="id-immo-data-pipeline_immo-network", #nom-dossier_immo-network
            mount_tmp_dir=False,
            docker_url="unix://var/run/docker.sock",
            auto_remove=True,
            force_pull=False,
        )
        tasks.append(task)

    tasks