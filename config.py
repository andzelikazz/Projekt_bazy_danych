API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "earthquakes"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

TIMEOUT_SECONDS = 30

MIN_MAGNITUDE = 2.5
IMPORT_INTERVAL_MINUTES = 30
IMPORT_LOOKBACK_HOURS = 3

SCHEMA_FILE = "schema.sql"
