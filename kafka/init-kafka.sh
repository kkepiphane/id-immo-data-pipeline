#!/bin/sh

until kafka-topics --bootstrap-server kafka:9092 --list >/dev/null 2>&1; do
  echo "Waiting for Kafka..."
  sleep 5
done

kafka-topics --create \
  --topic immo_raw \
  --bootstrap-server kafka:9092 \
  --replication-factor 1 \
  --partitions 1 || true

until kafka-topics --bootstrap-server kafka:9092 --describe --topic immo_raw 2>/dev/null | grep -q 'Leader:'; do
  echo "Waiting for partition leader..."
  sleep 2
done

echo "Topic ready!"