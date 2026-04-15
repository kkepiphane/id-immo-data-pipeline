from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime

with DAG(
    dag_id="weekly_scraping_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="0 2 * * 5",  # vendredi 02:00
    catchup=False
) as dag:

    scrape = DockerOperator(
        task_id="run_scrapers",
        image='immo_scraper:latest', 
        # On utilise 'command' pour DockerOperator
        command='bash -c "cd /app/ingestion && scrapy crawl omnisoft && scrapy crawl intendance && scrapy crawl igoe && scrapy crawl coinafrique"',
        network_mode='id-immo_immo-network',

        mount_tmp_dir=False,
        docker_url='unix://var/run/docker.sock',
        auto_remove=True,
        force_pull=False,
    ) 