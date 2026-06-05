import psycopg2
from psycopg2 import sql

from config import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER


def database_exists(cursor, database_name):
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
    return cursor.fetchone() is not None


def create_database():
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
    )
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            if database_exists(cursor, DB_NAME):
                print(f"Baza danych '{DB_NAME}' juz istnieje.")
                return

            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME))
            )
            print(f"Utworzono baze danych '{DB_NAME}'.")
    finally:
        connection.close()


if __name__ == "__main__":
    create_database()
