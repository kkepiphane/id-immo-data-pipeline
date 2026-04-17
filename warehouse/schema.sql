CREATE TABLE IF NOT EXISTS proprietes (
    listing_id TEXT,
    title TEXT,
    property_type TEXT,
    offer_type TEXT,
    description TEXT, 
    bedrooms TEXT,    
    square_footage TEXT,
    wc_interne TEXT,  
    legal_doc TEXT,   
    price BIGINT,
    address TEXT,     
    city TEXT,
    neighborhood TEXT,
    listing_url TEXT PRIMARY KEY,
    image_urls TEXT,
    source TEXT,
    scraped_at TEXT,   -- Changé en TEXT pour correspondre au StringType de Spark
    processed_at TIMESTAMP -- OBLIGATOIRE car ajouté par Spark
);