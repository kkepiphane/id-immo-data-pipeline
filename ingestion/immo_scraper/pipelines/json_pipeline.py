import json
from kafka import KafkaProducer


class KafkaPipeline:
    def open_spider(self, spider):
        # On se connecte à Kafka au lieu d'ouvrir un fichier
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
            acks='all',
            linger_ms=10,
            batch_size=16384,
            retries=5
        )

    def process_item(self, item, spider):
        try:
            self.producer.send('immo_raw', dict(item))
        except Exception as e:
            spider.logger.error(f"Kafka error: {e}")
        return item

    def close_spider(self, spider):
        self.producer.flush()  # On s'assure que tout est envoyé avant de fermer
        self.producer.close()