# Configuration de base
BOT_NAME = "immo_scraper"
SPIDER_MODULES = ["immo_scraper.spiders"]
NEWSPIDER_MODULE = "immo_scraper.spiders"

# --- Respect des serveurs et contournement (Anti-Block) ---
ROBOTSTXT_OBEY = False  
DOWNLOAD_DELAY = 2      
RANDOMIZE_DOWNLOAD_DELAY = True

# User-Agent complet pour ressembler à un vrai navigateur
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# --- Pipelines ---
ITEM_PIPELINES = {
   'immo_scraper.pipelines.json_pipeline.KafkaPipeline': 300,
}

# --- Encodage et Export (Crucial pour les accents comme Lomé, quartier...) ---
FEED_EXPORT_ENCODING = 'utf-8'
# Si tu veux aussi un backup CSV automatique en plus de Kafka
FEEDS = {
    'immobilier_total.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None, # Garde l'ordre des colonnes de ton Item
    },
}

# --- Paramètres de performance ---
CONCURRENT_REQUESTS = 16 
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60

# --- Gestion des logs ---
LOG_LEVEL = 'INFO'
