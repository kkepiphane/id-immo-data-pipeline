import scrapy
from datetime import datetime
import hashlib
import re
from ..items.immo_item import ProprieteItem

class CoinAfriqueSpider(scrapy.Spider):
    name = "coinafrique"
    
    start_urls = [
        "https://tg.coinafrique.com/categorie/immobilier"
    ]
    
    def parse(self, response):
        products = response.xpath('//div[contains(@class, "ad__card")]')
        
        for product in products:
            item = ProprieteItem()
            
            # URL
            url_path = product.xpath('.//a[contains(@class, "ad__card-image")]/@href').get()
            if not url_path:
                url_path = product.xpath('.//a[contains(@class, "card-image")]/@href').get()
            
            if not url_path:
                continue
                
            item["listing_url"] = response.urljoin(url_path)
            item["listing_id"] = hashlib.md5(item["listing_url"].encode()).hexdigest()
            
            # Titre
            title = product.xpath('.//p[contains(@class, "ad__card-description")]/a/text()').get(default="").strip()
            if not title:
                title = product.xpath('.//p[contains(@class, "title")]/a/text()').get(default="").strip()
            item["title"] = title
            
            # Prix
            price_raw = product.xpath('.//p[contains(@class, "ad__card-price")]/text()').get(default="0")
            price_numbers = re.findall(r'[\d\s]+', price_raw)
            item["price"] = re.sub(r'\s', '', price_numbers[0]) if price_numbers else "0"
            
            # Localisation
            location_full = product.xpath('.//p[contains(@class, "ad__card-location")]/span/text()').get(default="").strip()
            item["address"] = location_full
            
            # Extraction ville/quartier améliorée
            item["city"] = ""
            item["neighborhood"] = ""
            if "," in location_full:
                parts = [p.strip() for p in location_full.split(",")]
                item["neighborhood"] = parts[0]
                if len(parts) >= 2:
                    item["city"] = parts[-2] if "Togo" in parts[-1] and len(parts) >= 2 else parts[-1]
            else:
                item["city"] = location_full
            
            # Type de propriété
            title_lower = title.lower()
            type_mapping = {
                "terrain": "Terrain", "appartement": "Appartement",
                "villa": "Villa", "maison": "Maison", "studio": "Studio",
                "immeuble": "Immeuble"
            }
            item["property_type"] = next((v for k, v in type_mapping.items() if k in title_lower), "Autre")
            
            # Type d'offre
            if "location" in title_lower or "louer" in title_lower:
                item["offer_type"] = "Location"
            elif "vente" in title_lower or "vendre" in title_lower:
                item["offer_type"] = "Vente"
            else:
                item["offer_type"] = "Inconnu"
            
            # Image
            img_url = product.xpath('.//img[contains(@class, "ad__card-img")]/@src').get()
            item["image_urls"] = [img_url] if img_url else []
            
            # Métadonnées
            item["source"] = "coinafrique"
            item["scraped_at"] = datetime.now().isoformat()
            
            # Initialisation
            item["description"] = item["bedrooms"] = item["square_footage"] = item["wc_interne"] = None
            item["legal_doc"] = "Non spécifié"
            
            yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
        
        # Pagination avec sécurité
        next_link = response.xpath('//li[@class="pagination-indicator direction"]/a[contains(@href, "page")]/@href').get()
        if next_link and "page=2" in next_link:  # Limite simple
            yield response.follow(next_link, callback=self.parse)
    
    def parse_details(self, response):
        item = response.meta['item']
        
        # Description
        desc_parts = response.xpath('//div[contains(@class, "description")]//text()').getall()
        if not desc_parts:
            desc_parts = response.xpath('//div[contains(@class, "ad-description")]//text()').getall()
        item["description"] = " ".join([p.strip() for p in desc_parts if p.strip()])
        
        # Texte pour extraction
        main_text = " ".join(response.xpath('//div[contains(@class, "description")]//text() | //div[contains(@class, "details")]//text()').getall()).lower()
        
        # Surface
        for pattern in [r'(\d+)\s*m²', r'(\d+)\s*m2', r'surface\s*:?\s*(\d+)']:
            match = re.search(pattern, main_text)
            if match:
                item["square_footage"] = match.group(1)
                break
        
        # Pièces
        for pattern in [r'(\d+)\s*pièces?', r'(\d+)\s*chambres?']:
            match = re.search(pattern, main_text)
            if match:
                item["bedrooms"] = match.group(1)
                break
        
        # WC
        if re.search(r'\d+\s*wc|\d+\s*toilette', main_text):
            match = re.search(r'(\d+)\s*(?:wc|toilette)', main_text)
            item["wc_interne"] = match.group(1) if match else "1"
        
        # Documents légaux
        legal_found = [kw.capitalize() for kw in ['titre foncier', 'permis de construire', 'acte de vente'] if kw in main_text]
        if legal_found:
            item["legal_doc"] = ", ".join(legal_found)
        
        yield item