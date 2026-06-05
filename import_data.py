import argparse
import re
import time
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import Json
import requests

from config import (
    API_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    IMPORT_INTERVAL_MINUTES,
    IMPORT_LOOKBACK_HOURS,
    MIN_MAGNITUDE,
    TIMEOUT_SECONDS,
)


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def millis_to_datetime(value):
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def split_place(place):
    if not place:
        return None, None

    parts = [part.strip() for part in place.split(",")]
    first_part = parts[0]
    city = None

    if " of " in first_part:
        city = first_part.rsplit(" of ", 1)[1].strip() or None
    elif not re.match(r"^\d+(\.\d+)?\s*km\b", first_part, re.IGNORECASE):
        city = first_part or None

    if len(parts) == 1:
        return city, None

    return city, parts[-1]


def fetch_earthquakes(start_time=None, end_time=None, min_magnitude=MIN_MAGNITUDE):
    if end_time is None:
        end_time = datetime.now(timezone.utc)
    if start_time is None:
        start_time = end_time - timedelta(hours=IMPORT_LOOKBACK_HOURS)

    params = {
        "format": "geojson",
        "eventtype": "earthquake",
        "orderby": "time",
        "starttime": start_time.isoformat(),
        "endtime": end_time.isoformat(),
        "minmagnitude": min_magnitude,
    }

    response = requests.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def create_import_log(cursor):
    cursor.execute(
        """
        INSERT INTO imports (started_at, api_name, endpoint, import_status, imported_amount)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING import_id
        """,
        (
            datetime.now(timezone.utc),
            "USGS Earthquake Catalog",
            API_URL,
            False,
            0,
        ),
    )
    return cursor.fetchone()[0]


def finish_import_log(
    cursor,
    import_id,
    status,
    records_received,
    imported_amount,
    error_message=None,
):
    cursor.execute(
        """
        UPDATE imports
        SET finished_at = %s,
            records_received = %s,
            import_status = %s,
            imported_amount = %s,
            error_message = %s
        WHERE import_id = %s
        """,
        (
            datetime.now(timezone.utc),
            records_received,
            status,
            imported_amount,
            error_message,
            import_id,
        ),
    )


def get_or_create_category(cursor, category_name):
    if not category_name:
        category_name = "unknown"

    cursor.execute(
        """
        INSERT INTO category (category_name)
        VALUES (%s)
        ON CONFLICT (category_name)
        DO UPDATE SET category_name = EXCLUDED.category_name
        RETURNING category_id
        """,
        (category_name,),
    )
    return cursor.fetchone()[0]


def get_or_create_location(cursor, place):
    city, country = split_place(place)
    cursor.execute(
        """
        INSERT INTO location (place, city, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (place)
        DO UPDATE SET
            city = EXCLUDED.city,
            country = EXCLUDED.country
        RETURNING location_id
        """,
        (place or "unknown", city, country),
    )
    return cursor.fetchone()[0]


def save_event(cursor, feature, import_id):
    event_id = feature.get("id")
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or [None, None, None]

    if not event_id:
        return False

    longitude = coordinates[0] if len(coordinates) > 0 else None
    latitude = coordinates[1] if len(coordinates) > 1 else None
    depth = coordinates[2] if len(coordinates) > 2 else None
    place = properties.get("place") or properties.get("title") or "unknown"

    category_id = get_or_create_category(cursor, properties.get("type"))
    location_id = get_or_create_location(cursor, place)

    cursor.execute(
        """
        INSERT INTO coordinates (location_id, location, longitude, latitude)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (location_id)
        DO UPDATE SET
            location = EXCLUDED.location,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude
        """,
        (location_id, place, longitude, latitude),
    )

    cursor.execute(
        """
        INSERT INTO events (
            event_id, import_id, category_id, location_id, alert_level,
            event_time, updated_time, title, url, raw_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id)
        DO UPDATE SET
            import_id = EXCLUDED.import_id,
            category_id = EXCLUDED.category_id,
            location_id = EXCLUDED.location_id,
            alert_level = EXCLUDED.alert_level,
            updated_time = EXCLUDED.updated_time,
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            raw_json = EXCLUDED.raw_json
        """,
        (
            event_id,
            import_id,
            category_id,
            location_id,
            properties.get("alert"),
            millis_to_datetime(properties.get("time")),
            millis_to_datetime(properties.get("updated")),
            properties.get("title"),
            properties.get("url"),
            Json(feature),
        ),
    )

    cursor.execute(
        """
        INSERT INTO parameters (
            event_id, magnitude, depth, status, mmi, felt, tsunami,
            significance, magnitude_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id)
        DO UPDATE SET
            magnitude = EXCLUDED.magnitude,
            depth = EXCLUDED.depth,
            status = EXCLUDED.status,
            mmi = EXCLUDED.mmi,
            felt = EXCLUDED.felt,
            tsunami = EXCLUDED.tsunami,
            significance = EXCLUDED.significance,
            magnitude_type = EXCLUDED.magnitude_type
        """,
        (
            event_id,
            properties.get("mag"),
            depth,
            properties.get("status"),
            properties.get("mmi"),
            properties.get("felt"),
            bool(properties.get("tsunami")),
            properties.get("sig"),
            properties.get("magType"),
        ),
    )

    return True


def import_earthquakes(start_time=None, end_time=None, min_magnitude=MIN_MAGNITUDE):
    connection = get_connection()
    imported_amount = 0
    records_received = 0
    import_id = None

    try:
        with connection:
            with connection.cursor() as cursor:
                import_id = create_import_log(cursor)

        data = fetch_earthquakes(start_time, end_time, min_magnitude)
        features = data.get("features", [])
        records_received = len(features)

        with connection:
            with connection.cursor() as cursor:
                for feature in features:
                    if save_event(cursor, feature, import_id):
                        imported_amount += 1
                finish_import_log(
                    cursor,
                    import_id,
                    True,
                    records_received,
                    imported_amount,
                )

        print(f"Import zakonczony. Przetworzono zdarzen: {imported_amount}")
        return imported_amount
    except Exception as exc:
        with connection:
            with connection.cursor() as cursor:
                if import_id is not None:
                    finish_import_log(
                        cursor,
                        import_id,
                        False,
                        records_received,
                        imported_amount,
                        str(exc),
                    )
        raise
    finally:
        connection.close()


def run_cyclic_import():
    while True:
        try:
            import_earthquakes()
        except Exception as exc:
            print(f"Blad importu: {exc}")

        print(f"Nastepny import za {IMPORT_INTERVAL_MINUTES} minut.")
        time.sleep(IMPORT_INTERVAL_MINUTES * 60)


def parse_args():
    parser = argparse.ArgumentParser(description="Import trzesien ziemi z USGS do PostgreSQL.")
    parser.add_argument("--loop", action="store_true", help="Uruchom import cykliczny.")
    parser.add_argument("--min-magnitude", type=float, default=MIN_MAGNITUDE)
    parser.add_argument("--hours", type=int, default=IMPORT_LOOKBACK_HOURS)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.loop:
        run_cyclic_import()
    else:
        now = datetime.now(timezone.utc)
        import_earthquakes(
            start_time=now - timedelta(hours=args.hours),
            end_time=now,
            min_magnitude=args.min_magnitude,
        )
