import os
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SQL_PATH = PROJECT_ROOT / "sql" / "build_features.sql"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset.csv"

SNAPSHOT_DATES = [
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
    "2026-06-01",
    "2026-07-01",
    "2026-08-01",
]

COLUMNS = [
    "user_id",
    "country",
    "orders_last_60d",
    "sessions_last_60d",
    "avg_session_duration_60d",
    "events_last_60d",
    "page_views_60d",
    "product_views_60d",
    "searches_60d",
    "cart_additions_60d",
    "checkouts_60d",
    "target",
]


def build_dataset():
    load_dotenv(PROJECT_ROOT / ".env")

    params = {
        "host": os.getenv("PGHOST"),
        "port": os.getenv("PGPORT"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }

    query = SQL_PATH.read_text(encoding="utf-8")
    snapshots = []

    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:

            for snapshot_date in SNAPSHOT_DATES:
                cur.execute(query, (snapshot_date,))
                rows = cur.fetchall()

                df = pd.DataFrame(rows, columns=COLUMNS)
                df["snapshot_date"] = snapshot_date

                snapshots.append(df)

                print(
                    f"{snapshot_date}: "
                    f"{len(df)} пользователей"
                )

    combined = pd.concat(snapshots, ignore_index=True)

    combined["snapshot_date"] = pd.to_datetime(
        combined["snapshot_date"]
    )

    combined["avg_session_duration_60d"] = pd.to_numeric(
        combined["avg_session_duration_60d"],
        errors="coerce"
    )

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    combined.to_csv(DATA_PATH, index=False)

    print("\nДатасет успешно сохранён!")
    print("Путь:", DATA_PATH)
    print("Размер:", combined.shape)
    print("Распределение target:")
    print(combined["target"].value_counts())

    return combined


if __name__ == "__main__":
    build_dataset()


