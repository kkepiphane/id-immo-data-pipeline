CREATE TABLE IF NOT EXISTS proprietes (
    listing_id TEXT,
    title TEXT,
    property_type TEXT,
    offer_type TEXT,
    description TEXT, 
    bedrooms INTEGER,         -- Changé en INTEGER
    square_footage FLOAT,     -- Changé en FLOAT (pour les m2 précis)
    wc_interne INTEGER,  
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