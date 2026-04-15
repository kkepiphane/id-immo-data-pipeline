import scrapy
from datetime import datetime
from ..items.immo_item import ProprieteItem

class IgoeSpider(scrapy.Spider):
    name = "igoe"
    allowed_domains = ["igoeimmobilier.com"]
    start_urls = ["https://igoeimmobilier.com"]

    def parse(self, response):
        # On cible chaque carte de propriété
        listings = response.xpath('//div[contains(@class, "property-item")]')
        
        for ad in listings:
            item = ProprieteItem()
            
            # Titre et Lien
            item["title"] = ad.xpath('.//h3/a/text()').get(default="").strip()
            url = ad.xpath('.//h3/a/@href').get()
            item["listing_url"] = response.urljoin(url)
            
            # Prix (Extraction numérique)
            price_raw = ad.xpath('.//span[@class="price"]/text()').get(default="0")
            item["price"] = "".join(filter(str.isdigit, price_raw))
            
            # Localisation
            item["address"] = ad.xpath('.//span[@class="location"]/text()').get(default="").strip()
            item["city"] = "Lomé" # Majoritairement Lomé
            
            item["source"] = "igoeimmobilier"
            item["scraped_at"] = datetime.now().isoformat()
            
            if item["listing_url"]:
                yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
            else:
                yield item

        # Pagination (Bouton page suivante)
        next_page = response.xpath('//a[contains(@class, "next")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_details(self, response):
        item = response.meta['item']
        
        # Description
        desc = response.xpath('//div[contains(@class, "property-description")]//text()').getall()
        item["description"] = " ".join(desc).strip()
        
        # Extraction des caractéristiques via les labels spécifiques du site
        # On utilise une logique de recherche par texte car les IDs changent
        item["property_type"] = response.xpath('//li[contains(., "Type")]/span/text()').get()
        item["bedrooms"] = response.xpath('//li[contains(., "Chambres")]/span/text()').get()
        item["square_footage"] = response.xpath('//li[contains(., "Surface")]/span/text()').get()
        item["legal_doc"] = response.xpath('//li[contains(., "Document")]/span/text()').get()
        
        # Images (Galerie)
        item["image_urls"] = response.xpath('//div[@id="property-gallery"]//img/@src').getall()
        
        yield item
