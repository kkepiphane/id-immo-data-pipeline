FROM python:3.11-slim

ENV PYTHONPATH="/app/ingestion:$PYTHONPATH"
WORKDIR /app/ingestion

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ingestion/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion .

CMD ["scrapy", "list"]