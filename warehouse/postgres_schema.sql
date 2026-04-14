CREATE TABLE proprietes (
    listing_id TEXT PRIMARY KEY,
    title TEXT,
    price BIGINT,
    city TEXT,
    neighborhood TEXT,
    listing_url TEXT,
    scraped_at TIMESTAMP
);
