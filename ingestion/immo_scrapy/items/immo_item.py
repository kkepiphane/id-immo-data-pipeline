import scrapy

class MangaItem(scrapy.Item):

    title = scrapy.Field()

    categorie = scrapy.Field()

    rating = scrapy.Field()

    source = scrapy.Field()

    url = scrapy.Field()
    
    image = scrapy.Field()
    
    description = scrapy.Field()

    scraped_at = scrapy.Field()