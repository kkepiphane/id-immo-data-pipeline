import scrapy
from datetime import datetime
from ..items.immo_item import ProprieteItem # Utilise l'item qu'on a créé ensemble

class CoinAfriqueSpider(scrapy.Spider):
    name = "coinafrique"
    
    start_urls = [
        "https://tg.coinafrique.com/categorie/immobilier"
    ]
    
    def parse(self, response):
        # Sélecteur pour chaque carte d'annonce sur CoinAfrique
        products = response.xpath('//div[contains(@class, "card-container")]')
        
        for product in products:
            item = ProprieteItem()
            
            # Titre de l'annonce
            item["title"] = product.xpath('.//p[contains(@class, "title")]/text()').get(default="").strip()
            
            # Prix (on nettoie les espaces insécables et la devise)
            price_raw = product.xpath('.//p[contains(@class, "price")]/text()').get(default="0")
            item["price"] = price_raw.replace("CFA", "").replace(" ", "").strip()
            
            # Localisation (Ville, Quartier)
            item["address"] = product.xpath('.//p[contains(@class, "location")]/text()').get(default="").strip()
            
            # URL de l'annonce
            url_path = product.xpath('.//a[contains(@class, "card-image")]/@href').get()
            item["listing_url"] = response.urljoin(url_path) if url_path else None
            
            # Image principale
            item["image_urls"] = [product.xpath('.//img[contains(@class, "ad-image")]/@src').get()]
            
            # Métadonnées
            item["source"] = "coinafrique"
            item["scraped_at"] = datetime.now().isoformat()
            
            # Pour avoir les détails (surface, chambres), il faudrait suivre le lien
            if item["listing_url"]:
                yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
            else:
                yield item
        
        # Gestion de la pagination (Suivant)
        next_page = response.xpath('//ul[@class="pagination"]/li/a[@aria-label="Next"]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_details(self, response):
        item = response.meta['item']
        # Extraction de la description complète sur la page de l'annonce
        item["description"] = "".join(response.xpath('//div[contains(@class, "description")]//text()').getall()).strip()
        
        # Sur CoinAfrique, les caractéristiques sont souvent dans des badges
        item["property_type"] = response.xpath('//span[contains(@class, "category-badge")]/text()').get()
        
        yield item
