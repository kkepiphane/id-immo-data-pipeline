import scrapy
import json
from datetime import datetime
from immo_scraper.items.immo_item import ProprieteItem

class OmnisoftSpider(scrapy.Spider):
    name = "omnisoft"
    
    # L'URL de l'API reste la même
    api_url = "https://devapi.omnisoft.africa/public/api/v2"
    
    def start_requests(self):
        # Le corps de la requête GraphQL
        graphql_query = {
            "query": "query { getAllProperties(first: 2000) { data { id  titre descriptif piece surface cout_mensuel wc_douche_interne papier_propriete adresse {libelle} ville { denomination } quartier {denomination } offre { denomination } categorie_propriete { denomination } visuels { url } }}}"
        }
        
        # On envoie une requête POST avec le JSON
        yield scrapy.Request(
            url=self.api_url,
            method='POST',
            body=json.dumps(graphql_query),
            headers={'Content-Type': 'application/json'},
            callback=self.parse
        )

    def parse(self, response):
        data = json.loads(response.text)
        properties = data.get("data", {}).get("getAllProperties", {}).get("data", [])
        
        for prop in properties:
            item = ProprieteItem()
            
            # Données de base
            item["listing_id"] = prop.get("id")
            item["title"] = prop.get("titre")
            item["description"] = prop.get("descriptif")
            item["price"] = prop.get("cout_mensuel")
            item["bedrooms"] = int(prop.get("piece") or 0)
            item["square_footage"] = prop.get("surface")
            item["wc_interne"] = prop.get("wc_douche_interne")
            item["legal_doc"] = prop.get("papier_propriete")
            
            # Type de bien et type d'offre
            item["property_type"] = prop.get("categorie_propriete", {}).get("denomination") if prop.get("categorie_propriete") else None
            item["offer_type"] = prop.get("offre", {}).get("denomination") if prop.get("offre") else None
            
            # Localisation
            item["address"] = prop.get("adresse", {}).get("libelle") if prop.get("adresse") else None
            item["city"] = prop.get("ville", {}).get("denomination") if prop.get("ville") else None
            item["neighborhood"] = prop.get("quartier", {}).get("denomination") if prop.get("quartier") else None
            
            # Images
            visuels = prop.get("visuels", [])
            if visuels:
                # On s'assure que visuels est une liste pour éviter les erreurs
                item["image_urls"] = [v.get("url") for v in visuels if v.get("url")]
            
            # URL de l'annonce (Correction de l'URL immoask)
            item["listing_url"] = f"https://devapi.omnisoft.africa/property/{prop.get('id')}"
            # item["listing_url"] = f"https://immoask.com{prop.get('id')}"
            
            item["source"] = "omnisoft_api"
            item["scraped_at"] = datetime.now().isoformat()
            
            yield item