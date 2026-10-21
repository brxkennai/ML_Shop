import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    load_dotenv(PROJECT_ROOT / ".env")
    params = {
        "host": os.getenv("PGHOST"),
        "port": os.getenv("PGPORT"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }
    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE country = 'RU';")
            result = cur.fetchone()
    print("Количество RU пользователей:", result[0])


if __name__ == "__main__":
    main()
