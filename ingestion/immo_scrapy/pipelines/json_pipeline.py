import json
from kafka import KafkaProducer


class KafkaPipeline:
    def open_spider(self, spider):
        # On se connecte à Kafka au lieu d'ouvrir un fichier
        self.producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(
                v, ensure_ascii=False).encode('utf-8')
        )

    def process_item(self, item, spider):
        # On envoie l'item dans le "tuyau" Kafka
        # C'est ultra rapide car c'est envoyé en mémoire
        self.producer.send('immo_raw', dict(item))
        return item

    def close_spider(self, spider):
        self.producer.flush()  # On s'assure que tout est envoyé avant de fermer
        self.producer.close()