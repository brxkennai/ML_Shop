
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

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
