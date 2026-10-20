"""Import generated CSV files into PostgreSQL. Run after 01_create_tables.sql."""
import argparse
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

TABLES = ['users', 'sessions', 'events', 'orders', 'payments', 'support_tickets']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=Path('data'))
    args = parser.parse_args()
    load_dotenv()
    params = {
        'host': os.getenv('PGHOST', 'localhost'),
        'port': os.getenv('PGPORT', '5432'),
        'dbname': os.getenv('PGDATABASE', 'ml_shop'),
        'user': os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('PGPASSWORD'),
    }
    with psycopg.connect(**params) as conn:
        with conn.cursor() as cur:
            for table in TABLES:
                filename = args.data / f'{table}.csv'
                if not filename.is_file():
                    raise FileNotFoundError(filename)
                with filename.open('rb') as f:
                    # COPY supports CSV, header skipping, NULL for missing values.
                    with cur.copy(f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')") as copy:
                        while chunk := f.read(1024 * 1024):
                            copy.write(chunk)
                print(f'Loaded {table}')
    print('Done. Check tables in pgAdmin. Avoid running twice without clearing tables.')


if __name__ == '__main__':
    main()
