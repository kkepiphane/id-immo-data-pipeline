FROM apache/spark:3.4.2

USER root

# Installer Java 11
RUN apt-get update && apt-get install -y openjdk-11-jdk curl \
    && rm -rf /var/lib/apt/lists/*

# Variables Java & spark
ENV SPARK_HOME=/opt/spark
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$SPARK_HOME/bin:$JAVA_HOME/bin:$PATH
ENV PYSPARK_SUBMIT_ARGS="--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.2 pyspark-shell"

# JDBC PostgreSQL
COPY postgresql-42.6.2.jar /opt/spark/jars/

# Jobs Spark
COPY jobs/ /opt/spark/jobs/
WORKDIR /opt/spark/jobs

# Entrypoint
COPY spark-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 4040 7077 8080 8081

ENTRYPOINT ["/entrypoint.sh"]