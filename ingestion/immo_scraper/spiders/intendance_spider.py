import scrapy
from datetime import datetime
import hashlib
import re
import json
from ..items.immo_item import ProprieteItem

class IntendanceSpider(scrapy.Spider):
    name = "intendance"
    allowed_domains = ["intendance.tg"]
    start_urls = ["https://intendance.tg"]
    
    def parse(self, response):
        # 1. Extraire les annonces du slider (carrousel)
        slider_items = response.xpath('//div[contains(@class, "slider_prop_wrapper")]//div[contains(@class, "listing_wrapper")]')
        
        for ad in slider_items:
            yield from self.extract_property(ad, response)
        
        # 2. Extraire les annonces de la grille principale
        grid_items = response.xpath('//div[contains(@class, "listing_wrapper")]')
        
        for ad in grid_items:
            # Éviter les doublons avec le slider
            if ad not in slider_items:
                yield from self.extract_property(ad, response)
        
        # 3. Gérer le bouton "Découvrir" - besoin de trouver l'URL AJAX
        # Regarder dans le code JavaScript ou les attributs data-*
        
        # Chercher l'URL de chargement AJAX
        load_more_script = response.xpath('//script[contains(text(), "wpestate_property_list_sh")]/text()').get()
        if load_more_script:
            # Extraire l'URL de l'API si présente
            api_url_match = re.search(r'ajaxurl\s*:\s*["\']([^"\']+)["\']', load_more_script)
            if api_url_match:
                api_url = api_url_match.group(1)
                # Déclencher le chargement des annonces supplémentaires
                yield scrapy.FormRequest(
                    url=api_url,
                    formdata={'action': 'wpestate_ajax_load_more', 'page': '2'},
                    callback=self.parse_ajax_listings,
                    headers={'X-Requested-With': 'XMLHttpRequest'}
                )
        
        # 4. Pagination standard
        next_page = response.xpath('//a[@aria-label="Next"]/@href').get()
        if next_page and "page" in next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def extract_property(self, ad, response):
        """Extrait les données d'une annonce"""
        item = ProprieteItem()
        
        # URL et ID
        url = ad.xpath('.//h4/a/@href').get()
        if not url:
            url = ad.xpath('.//a[contains(@class, "property_listing")]/@data-link').get()
        
        if url:
            item["listing_url"] = response.urljoin(url)
            item["listing_id"] = hashlib.md5(item["listing_url"].encode()).hexdigest()
        else:
            return
        
        # Titre
        title = ad.xpath('.//h4/a/text()').get(default="").strip()
        if not title:
            title = ad.xpath('.//a[contains(@class, "property_listing")]/@data-modal-title').get(default="")
        item["title"] = title
        
        # Prix
        price_raw = ad.xpath('.//div[contains(@class, "listing_unit_price_wrapper")]/text()').get(default="0")
        if not price_raw:
            price_raw = ad.xpath('.//span[contains(@class, "listing_unit_price")]/text()').get(default="0")
        
        # Nettoyer le prix (garder uniquement les chiffres)
        price_numbers = re.findall(r'[\d\s]+', price_raw)
        if price_numbers:
            item["price"] = re.sub(r'\s', '', price_numbers[0])
        else:
            item["price"] = "0"
        
        # Localisation
        location_text = ad.xpath('.//div[contains(@class, "property_location_image")]//text()').getall()
        location_full = " ".join(location_text).strip()
        item["address"] = location_full
        
        # Extraction ville/quartier
        neighborhood_elem = ad.xpath('.//a[@rel="tag"][1]/text()').get()
        city_elem = ad.xpath('.//a[@rel="tag"][2]/text()').get()
        
        item["neighborhood"] = neighborhood_elem.strip() if neighborhood_elem else ""
        item["city"] = city_elem.strip() if city_elem else "Lomé"
        
        # Type de propriété (déduit du titre)
        title_lower = title.lower()
        if "appartement" in title_lower:
            item["property_type"] = "Appartement"
        elif "villa" in title_lower:
            item["property_type"] = "Villa"
        elif "maison" in title_lower:
            item["property_type"] = "Maison"
        elif "terrain" in title_lower:
            item["property_type"] = "Terrain"
        else:
            item["property_type"] = "Autre"
        
        # Type d'offre
        offer_badge = ad.xpath('.//div[contains(@class, "action_tag_wrapper")]/text()').get(default="")
        if "Location" in offer_badge or "Locations" in offer_badge:
            item["offer_type"] = "Location"
        elif "Vente" in offer_badge or "Ventes" in offer_badge:
            item["offer_type"] = "Vente"
        else:
            item["offer_type"] = "Inconnu"
        
        # Nombre de pièces (chambres)
        rooms_icon = ad.xpath('.//span[contains(@class, "inforoom")]/text()').get()
        if rooms_icon:
            item["bedrooms"] = re.sub(r'\D', '', rooms_icon)  # Garder uniquement les chiffres
        
        # Nombre de sanitaires
        baths_icon = ad.xpath('.//span[contains(@class, "infobath")]/text()').get()
        if baths_icon:
            item["wc_interne"] = re.sub(r'\D', '', baths_icon)
        
        # Surface
        size_icon = ad.xpath('.//span[contains(@class, "infosize")]//text()').get()
        if size_icon:
            size_match = re.search(r'(\d+)', size_icon)
            if size_match:
                item["square_footage"] = size_match.group(1)
        
        # Description courte (peut être complétée dans parse_details)
        short_desc = ad.xpath('.//div[contains(@class, "listing_details")]/text()').get(default="").strip()
        item["description"] = short_desc
        
        # Image
        img_url = ad.xpath('.//img[contains(@class, "wp-post-image")]/@src').get()
        if img_url:
            item["image_urls"] = [img_url]
        else:
            item["image_urls"] = []
        
        # Métadonnées
        item["source"] = "intendance.tg"
        item["scraped_at"] = datetime.now().isoformat()
        
        # Initialisation des champs manquants
        item.setdefault("legal_doc", "Non spécifié")
        
        # Aller chercher les détails supplémentaires si l'URL existe
        if item["listing_url"]:
            yield scrapy.Request(item["listing_url"], callback=self.parse_details, meta={'item': item})
        else:
            yield item
    
    def parse_ajax_listings(self, response):
        """Gère le chargement AJAX des annonces supplémentaires"""
        try:
            data = json.loads(response.text)
            if data.get('html'):
                # Créer un faux sélecteur Scrapy à partir du HTML retourné
                fake_response = scrapy.Selector(text=data['html'])
                new_listings = fake_response.xpath('//div[contains(@class, "listing_wrapper")]')
                
                for ad in new_listings:
                    yield from self.extract_property(ad, response)
                
                # Vérifier s'il y a une page suivante
                if data.get('loadmore') and data['loadmore'] != 'no_more':
                    # Continuer à charger
                    yield scrapy.FormRequest(
                        url=response.url,
                        formdata={'action': 'wpestate_ajax_load_more', 'page': str(data.get('next_page', 2))},
                        callback=self.parse_ajax_listings,
                        headers={'X-Requested-With': 'XMLHttpRequest'}
                    )
        except json.JSONDecodeError:
            self.logger.warning("Réponse AJAX non-JSON reçue")
    
    def parse_details(self, response):
        """Extrait les détails d'une annonce individuelle"""
        item = response.meta['item']
        
        # Description complète
        desc_paragraphs = response.xpath('//div[@id="description"]//p/text()').getall()
        if not desc_paragraphs:
            desc_paragraphs = response.xpath('//div[contains(@class, "property_description")]//text()').getall()
        
        if desc_paragraphs:
            item["description"] = " ".join([p.strip() for p in desc_paragraphs if p.strip()])
        
        # Tableau des caractéristiques
        details_table = response.xpath('//ul[contains(@class, "property_details_list")]')
        
        # Surface
        if not item.get("square_footage"):
            size_text = response.xpath('//li[contains(text(), "Surface") or contains(text(), "Superficie")]/following-sibling::li/text()').get()
            if not size_text:
                size_text = response.xpath('//strong[contains(text(), "Surface")]/following-sibling::text()').get()
            if size_text:
                size_match = re.search(r'(\d+)', size_text)
                if size_match:
                    item["square_footage"] = size_match.group(1)
        
        # Nombre de chambres
        if not item.get("bedrooms"):
            rooms_text = response.xpath('//li[contains(text(), "Chambres") or contains(text(), "Pièces")]/following-sibling::li/text()').get()
            if rooms_text:
                rooms_match = re.search(r'(\d+)', rooms_text)
                if rooms_match:
                    item["bedrooms"] = rooms_match.group(1)
        
        # Sanitaires
        if not item.get("wc_interne"):
            baths_text = response.xpath('//li[contains(text(), "Salle de bain") or contains(text(), "Douche")]/following-sibling::li/text()').get()
            if baths_text:
                baths_match = re.search(r'(\d+)', baths_text)
                if baths_match:
                    item["wc_interne"] = baths_match.group(1)
        
        # Type de propriété (si non détecté)
        if item.get("property_type") == "Autre" or not item.get("property_type"):
            type_text = response.xpath('//li[contains(text(), "Type")]/following-sibling::li/text()').get()
            if type_text:
                item["property_type"] = type_text.strip()
        
        # Images supplémentaires
        all_images = response.xpath('//div[contains(@class, "owl-carousel")]//img/@src').getall()
        if all_images and not item.get("image_urls"):
            item["image_urls"] = all_images
        elif all_images and item.get("image_urls"):
            # Fusionner les images
            existing = item["image_urls"]
            item["image_urls"] = list(set(existing + all_images))
        
        # Documents légaux (recherche dans la description)
        if "titre foncier" in item["description"].lower():
            item["legal_doc"] = "Titre foncier"
        elif "permis de construire" in item["description"].lower():
            item["legal_doc"] = "Permis de construire"
        elif "acte de vente" in item["description"].lower():
            item["legal_doc"] = "Acte de vente"
        
        yield item