import json
from kafka import KafkaProducer


class KafkaPipeline:

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self):
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )

    def process_item(self, item):
        self.producer.send('immo_raw', dict(item))
        return item

    def close_spider(self):
        self.producer.flush()
        self.producer.close()