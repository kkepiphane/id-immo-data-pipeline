import scrapy

class ProprieteItem(scrapy.Item):
    # Identifiants et liens
    listing_id = scrapy.Field()
    title = scrapy.Field()
    listing_url = scrapy.Field()
    
    # Caractéristiques du bien
    property_type = scrapy.Field()  
    offer_type = scrapy.Field()     # Vente, Location
    description = scrapy.Field()
    bedrooms = scrapy.Field()       # Nombre de pièces
    square_footage = scrapy.Field() # Surface
    wc_interne = scrapy.Field()     # Sanitaires
    legal_doc = scrapy.Field()      # Papiers (Titre foncier, etc.)
    
    # Prix et Localisation
    price = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    neighborhood = scrapy.Field()   # Quartier
    
    # Multimédia et Meta
    image_urls = scrapy.Field()     # Liste des URLs d'images
    source = scrapy.Field()
    scraped_at = scrapy.Field()
