import scrapy
from datetime import datetime
from ..items.immo_item import ProprieteItem

class IntendanceSpider(scrapy.Spider):
    name = "intendance"
    allowed_domains = ["intendance.tg"]
    start_urls = ["https://intendance.tg"]

    def parse(self, response):
        # On cible chaque bloc d'annonce
        listings = response.xpath('//div[contains(@class, "listing_wrapper")]')
        
        for ad in listings:
            item = ProprieteItem()
            
            # Extraction des infos de base sur la carte
            item["title"] = ad.xpath('.//h4/a/text()').get(default="").strip()
            url = ad.xpath('.//h4/a/@href').get()
            item["listing_url"] = response.urljoin(url)
            
            # Prix : on ne garde que les chiffres
            price_raw = ad.xpath('.//span[@class="listing_unit_price"]/text()').get(default="0")
            item["price"] = "".join(filter(str.isdigit, price_raw))
            
            item["neighborhood"] = ad.xpath('.//div[@class="listing_location"]/a/text()').get()
            item["city"] = "Lomé"
            item["source"] = "intendance.tg"
            item["scraped_at"] = datetime.now().isoformat()
            
            # Aller chercher les détails sur la page de l'annonce
            if item["listing_url"]:
                yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
            else:
                yield item

        # Pagination : bouton "Suivant"
        next_page = response.xpath('//a[@aria-label="Next"]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_details(self, response):
        item = response.meta['item']
        
        # Description
        desc = response.xpath('//div[@id="description"]//p/text()').getall()
        item["description"] = " ".join(desc).strip()
        
        # Caractéristiques spécifiques (Surface, Type, etc.)
        item["square_footage"] = response.xpath('//strong[contains(text(), "Surface")]/following-sibling::text()').get()
        item["property_type"] = response.xpath('//li[contains(text(), "Type")]/strong/text()').get()
        item["bedrooms"] = response.xpath('//span[contains(@data-original-title, "Chambres")]/following-sibling::text()').get()
        
        # Images
        item["image_urls"] = response.xpath('//div[contains(@class, "owl-carousel")]//img/@src').getall()
        
        yield item
