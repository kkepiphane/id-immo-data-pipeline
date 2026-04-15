from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "immo_admin",
    "retries": 1,
}

with DAG(
    dag_id="immo_scraping_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 0 * * *",  # Une fois par jour à minuit
    catchup=False,
) as dag:

    run_spiders = BashOperator(
        task_id="run_spiders",
        bash_command="'scrapy crawl omnisoft && scrapy crawl intendance && scrapy crawl igoe && scrapy crawl coinafrique'",
    )
