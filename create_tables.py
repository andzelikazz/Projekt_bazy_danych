from pathlib import Path

import psycopg2

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER, SCHEMA_FILE


def create_tables():
    schema_path = Path(__file__).with_name(SCHEMA_FILE)
    schema_sql = schema_path.read_text(encoding="utf-8")

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(schema_sql)
        print("Utworzono lub zaktualizowano tabele.")
    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
