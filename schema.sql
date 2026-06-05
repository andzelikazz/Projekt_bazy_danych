CREATE TABLE IF NOT EXISTS imports (
    import_id SERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    api_name VARCHAR(100) NOT NULL DEFAULT 'USGS Earthquake Catalog',
    endpoint TEXT NOT NULL DEFAULT 'https://earthquake.usgs.gov/fdsnws/event/1/query',
    records_received INTEGER NOT NULL DEFAULT 0,
    import_status BOOLEAN NOT NULL DEFAULT FALSE,
    imported_amount INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS location (
    location_id SERIAL PRIMARY KEY,
    place VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100),
    city VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS coordinates (
    location_id INTEGER PRIMARY KEY,
    location VARCHAR(255),
    longitude NUMERIC(10,6),
    latitude NUMERIC(10,6),

    CONSTRAINT fk_coordinates_location
        FOREIGN KEY (location_id)
        REFERENCES location(location_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(50) PRIMARY KEY,
    import_id INTEGER NOT NULL,
    category_id INTEGER,
    location_id INTEGER,
    alert_level VARCHAR(20),
    event_time TIMESTAMPTZ,
    updated_time TIMESTAMPTZ,
    title TEXT,
    url TEXT,
    raw_json JSONB NOT NULL,

    CONSTRAINT fk_event_import
        FOREIGN KEY (import_id)
        REFERENCES imports(import_id),

    CONSTRAINT fk_event_category
        FOREIGN KEY (category_id)
        REFERENCES category(category_id),

    CONSTRAINT fk_event_location
        FOREIGN KEY (location_id)
        REFERENCES location(location_id)
);

CREATE TABLE IF NOT EXISTS parameters (
    event_id VARCHAR(50) PRIMARY KEY,
    magnitude NUMERIC(4,2),
    depth NUMERIC(8,2),
    status VARCHAR(50),
    mmi NUMERIC(4,2),
    felt INTEGER,
    tsunami BOOLEAN,
    significance INTEGER,
    magnitude_type VARCHAR(20),

    CONSTRAINT fk_parameters_event
        FOREIGN KEY (event_id)
        REFERENCES events(event_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_events_event_time ON events(event_time);
CREATE INDEX IF NOT EXISTS idx_parameters_magnitude ON parameters(magnitude);

ALTER TABLE IF EXISTS imports
    ADD COLUMN IF NOT EXISTS api_name VARCHAR(100) NOT NULL DEFAULT 'USGS Earthquake Catalog';

ALTER TABLE IF EXISTS imports
    ADD COLUMN IF NOT EXISTS endpoint TEXT NOT NULL DEFAULT 'https://earthquake.usgs.gov/fdsnws/event/1/query';

ALTER TABLE IF EXISTS imports
    ADD COLUMN IF NOT EXISTS records_received INTEGER NOT NULL DEFAULT 0;

ALTER TABLE IF EXISTS events
    ADD COLUMN IF NOT EXISTS raw_json JSONB;

ALTER TABLE IF EXISTS coordinates
    ADD COLUMN IF NOT EXISTS location VARCHAR(255);
