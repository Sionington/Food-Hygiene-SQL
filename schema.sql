DROP TABLE IF EXISTS establishments;
DROP TABLE IF EXISTS authorities;

CREATE TABLE authorities (
    authority_id INTEGER PRIMARY KEY,
    authority_name TEXT,
    establishment_count INTEGER,
    authority_id_code TEXT UNIQUE
);

CREATE TABLE establishments (
    establishment_id INTEGER PRIMARY KEY,
    authority_id_code TEXT REFERENCES authorities(authority_id_code),
    establishment_name TEXT,
    rating_value TEXT,
    business_type TEXT,
    post_code TEXT,
    rating_date TEXT
);
