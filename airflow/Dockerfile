FROM apache/airflow:2.8.3

USER root

# Installer dépendances système
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

# Installer packages Python
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.7.0 \
    apache-airflow-providers-http==4.5.1 \
    requests \
    psycopg2-binary

WORKDIR /opt/airflow