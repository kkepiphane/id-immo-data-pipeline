ITEM_PIPELINES = {
   'immo_scraper.pipelines.json_pipeline.KafkaPipeline': 300,
}

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 2

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

BOT_NAME = "immo_scraper"

SPIDER_MODULES = ["immo_scraper.spiders"]
NEWSPIDER_MODULE = "immo_scraper.spiders"