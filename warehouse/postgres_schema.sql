CREATE TABLE proprietes (
    listing_id TEXT PRIMARY KEY,
    title TEXT,
    property_type TEXT,
    offer_type TEXT,
    price BIGINT,
    square_footage TEXT,
    city TEXT,
    neighborhood TEXT,
    listing_url TEXT,
    image_urls TEXT, -- Stocké comme texte ou JSON
    source TEXT,
    scraped_at TIMESTAMP
);
