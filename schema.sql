DROP TABLE IF EXISTS establishments;
DROP TABLE IF EXISTS authorities;

CREATE TABLE authorities (
    AuthorityID INTEGER PRIMARY KEY,
    AuthorityName TEXT,
    EstablishmentCount INTEGER,
    AuthorityIDCode TEXT UNIQUE
);

CREATE TABLE establishments (
    EstablishmentID INTEGER PRIMARY KEY,
    AuthorityIDCode TEXT REFERENCES authorities(AuthorityIDCode),
    EstablishmentName TEXT,
    RatingValue TEXT,
    BusinessType TEXT,
    PostCode TEXT,
    RatingDate TEXT
);
