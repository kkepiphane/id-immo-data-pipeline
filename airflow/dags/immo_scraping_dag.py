from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "manga",
    "retries": 1,
}

with DAG(
    dag_id="manga_scraping_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 */6 * * *",  # toutes les 6h
    catchup=False,
) as dag:

    scrape_senscritique = BashOperator(
        task_id="scrape_senscritique",
        bash_command="docker exec manga_scraper scrapy crawl senscritique",
    )

    scrape_topito = BashOperator(
        task_id="scrape_topito",
        bash_command="docker exec manga_scraper scrapy crawl topito",
    )

    scrape_senscritique >> scrape_topito