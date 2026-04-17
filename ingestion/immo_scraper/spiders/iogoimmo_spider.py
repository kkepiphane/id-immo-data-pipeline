import scrapy
from datetime import datetime
import hashlib
import re
from ..items.immo_item import ProprieteItem

class IgoeSpider(scrapy.Spider):
    name = "igoe"
    allowed_domains = ["igoeimmobilier.com"]
    start_urls = ["https://www.igoeimmobilier.com/les-annonces/"]
    
    def parse(self, response):
        # Sélecteur correct pour chaque annonce
        listings = response.xpath('//div[contains(@class, "epl-listing-post")]')
        
        for ad in listings:
            item = ProprieteItem()
            
            # URL et ID
            url = ad.xpath('.//h3[@class="entry-title"]/a/@href').get()
            if not url:
                url = ad.xpath('.//a[@class="epl-more-link"]/@href').get()
            
            if url:
                item["listing_url"] = response.urljoin(url)
                item["listing_id"] = hashlib.md5(item["listing_url"].encode()).hexdigest()
            else:
                continue
            
            # Titre
            title = ad.xpath('.//h3[@class="entry-title"]/a/text()').get(default="").strip()
            if not title:
                title = ad.xpath('.//h3[@class="entry-title"]/text()').get(default="").strip()
            item["title"] = title
            
            # Prix
            price_text = ad.xpath('.//div[@class="price"]/span/text()').get(default="")
            if not price_text:
                price_text = ad.xpath('.//span[@class="page-price sold-status"]/text()').get(default="")
            if not price_text:
                price_text = ad.xpath('.//span[@class="page-price"]/text()').get(default="")
            
            # Extraction des chiffres du prix
            price_numbers = re.findall(r'[\d\s\.]+', price_text)
            if price_numbers:
                raw_price = price_numbers[0].replace('.', '').replace(' ', '')
                item["price"] = raw_price if raw_price else "0"
            else:
                item["price"] = "0"
            
            # Quartier
            neighborhood = ad.xpath('.//span[@class="item-suburb"]/text()').get(default="").strip()
            item["neighborhood"] = neighborhood
            item["city"] = "Lomé"  # Toutes les annonces semblent être à Lomé
            item["address"] = f"{neighborhood}, Lomé" if neighborhood else "Lomé"
            
            # Type d'offre
            offer_badge = ad.xpath('.//span[contains(@class, "status-sticker")]/text()').get(default="")
            if "louer" in offer_badge.lower():
                item["offer_type"] = "Location"
            elif "vente" in offer_badge.lower():
                item["offer_type"] = "Vente"
            else:
                item["offer_type"] = "Inconnu"
            
            # Caractéristiques depuis les icônes EPL
            # Nombre de chambres
            bedrooms_icon = ad.xpath('.//div[contains(@class, "epl-icon-container-bed")]//div[@class="icon-value"]/text()').get()
            if bedrooms_icon:
                item["bedrooms"] = bedrooms_icon.strip()
            
            # Nombre de salles de bain
            baths_icon = ad.xpath('.//div[contains(@class, "epl-icon-container-bath")]//div[@class="icon-value"]/text()').get()
            if baths_icon:
                item["wc_interne"] = baths_icon.strip()
            
            # Stationnement (peut être utilisé comme information complémentaire)
            parking_icon = ad.xpath('.//div[contains(@class, "epl-icon-container-car")]//div[@class="icon-value"]/text()').get()
            
            # Type de propriété (déduit du titre ou de la description)
            title_lower = title.lower()
            desc_text = ad.xpath('.//div[@class="epl-excerpt-content"]/p/text()').get(default="").lower()
            full_text = title_lower + " " + desc_text
            
            if "villa" in full_text:
                item["property_type"] = "Villa"
            elif "appartement" in full_text:
                item["property_type"] = "Appartement"
            elif "terrain" in full_text:
                item["property_type"] = "Terrain"
            elif "studio" in full_text:
                item["property_type"] = "Studio"
            else:
                item["property_type"] = "Maison" if "maison" in full_text else "Autre"
            
            # Description courte
            short_desc = ad.xpath('.//div[@class="epl-excerpt-content"]/p/text()').get(default="").strip()
            item["description"] = short_desc
            
            # Image
            img_url = ad.xpath('.//img[contains(@class, "wp-post-image")]/@src').get()
            if img_url:
                item["image_urls"] = [img_url]
            else:
                item["image_urls"] = []
            
            # Métadonnées
            item["source"] = "igoeimmobilier"
            item["scraped_at"] = datetime.now().isoformat()
            
            # Initialisation des champs qui seront complétés dans parse_details
            item["square_footage"] = ""
            item["legal_doc"] = ""
            
            # Aller chercher les détails sur la page individuelle
            yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
        
        # Gestion de la pagination
        # Note: Le site semble utiliser le chargement infini (AJAX)
        # Chercher un éventuel bouton "Charger plus" ou "Suivant"
        next_button = response.xpath('//a[contains(@class, "next") or contains(text(), "Suivant")]/@href').get()
        if next_button:
            yield response.follow(next_button, callback=self.parse)
        else:
            # Alternative: chercher un attribut data-page ou similaire
            load_more = response.xpath('//div[contains(@class, "load-more")]/a/@href').get()
            if load_more:
                yield response.follow(load_more, callback=self.parse)
    
    def parse_details(self, response):
        item = response.meta['item']
        
        # Description complète
        desc_paragraphs = response.xpath('//div[contains(@class, "entry-content")]//p/text()').getall()
        if not desc_paragraphs:
            desc_paragraphs = response.xpath('//div[contains(@class, "property-description")]//text()').getall()
        
        if desc_paragraphs:
            full_desc = " ".join([p.strip() for p in desc_paragraphs if p.strip()])
            if item["description"]:
                item["description"] = item["description"] + " " + full_desc
            else:
                item["description"] = full_desc
        
        # Surface depuis la page de détail
        surface_text = response.xpath('//li[contains(., "Surface") or contains(., "superficie")]/text()').get()
        if not surface_text:
            surface_text = response.xpath('//div[contains(@class, "epl-icon-container-size")]//div[@class="icon-value"]/text()').get()
        
        if surface_text:
            surface_match = re.search(r'(\d+)', surface_text)
            if surface_match:
                item["square_footage"] = surface_match.group(1)
        
        # Documents légaux (recherche dans la description)
        if item["description"]:
            desc_lower = item["description"].lower()
            if "titre foncier" in desc_lower:
                item["legal_doc"] = "Titre foncier"
            elif "permis de construire" in desc_lower:
                item["legal_doc"] = "Permis de construire"
            elif "acte de vente" in desc_lower:
                item["legal_doc"] = "Acte de vente"
            else:
                item["legal_doc"] = "Non spécifié"
        
        # Images supplémentaires depuis la galerie
        gallery_images = response.xpath('//div[contains(@class, "property-gallery")]//img/@src').getall()
        if not gallery_images:
            gallery_images = response.xpath('//div[@id="property-gallery"]//img/@src').getall()
        
        if gallery_images and item["image_urls"]:
            # Fusionner sans doublons
            all_images = set(item["image_urls"] + gallery_images)
            item["image_urls"] = list(all_images)
        elif gallery_images:
            item["image_urls"] = gallery_images
        
        yield item