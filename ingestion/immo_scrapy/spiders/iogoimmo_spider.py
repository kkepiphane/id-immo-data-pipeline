import scrapy
from datetime import datetime
from ..items.manga_item import MangaItem

class SensCritiqueSpider(scrapy.Spider):
    name = "senscritique"
    
    start_urls = [
        "https://www.igoeimmobilier.com"
    ]
    
    def parse(self, response):
        products = response.xpath('//div[contains(@class, "sc-b5c2c6dc-1")]')
        
        for product in products:
            item = MangaItem()
            
           
            title_elem = product.xpath('.//h2[contains(@class, "sc-f84047c3-1")]/a/text()').get()
            if title_elem:
                item["title"] = title_elem.strip()
            
            rating_elem = product.xpath('.//span[contains(@class, "ezSuwK")]/text()').get()
            if rating_elem:
                item["rating"] = rating_elem.strip()
            
            genre_elems = product.xpath('.//a[contains(@href, "genre")]/text()').getall()
            item["genre"] = [g.strip() for g in genre_elems if g.strip()]
            
           
            url_elem = product.xpath('.//h2[contains(@class, "sc-f84047c3-1")]/a/@href').get()
            if url_elem:
                item["url"] = response.urljoin(url_elem)
            else:
                item["url"] = response.url
            
            item["source"] = "senscritique"
            item["scraped_at"] = datetime.now().isoformat()
            
            yield item
        
        next_page = response.xpath('//a[contains(@rel, "next")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)