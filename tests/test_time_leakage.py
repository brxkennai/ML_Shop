import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv
from psycopg.rows import dict_row


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = PROJECT_ROOT / "sql" / "build_features.sql"

QUERY = SQL_PATH.read_text(encoding="utf-8")
SNAPSHOT_DATE = "2026-07-01"


@pytest.fixture
def test_db():
    load_dotenv(PROJECT_ROOT / ".env")

    params = {
        "host": os.getenv("PGHOST"),
        "port": os.getenv("PGPORT"),
        "dbname": os.getenv("PGDATABASE"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
    }

    with psycopg.connect(
        **params,
        row_factory=dict_row
    ) as conn:
        with conn.cursor() as cur:
            # Все таблицы создаём временными.
            # Реальную базу данных не изменяем.
            cur.execute(
                "SET LOCAL search_path TO pg_temp, public"
            )

            cur.execute("""
                CREATE TEMP TABLE users (
                    user_id INTEGER,
                    country TEXT
                )
            """)

            cur.execute("""
                CREATE TEMP TABLE sessions (
                    session_id INTEGER,
                    user_id INTEGER,
                    started_at TIMESTAMP,
                    duration_seconds NUMERIC
                )
            """)

            cur.execute("""
                CREATE TEMP TABLE orders (
                    order_id INTEGER,
                    user_id INTEGER,
                    created_at TIMESTAMP,
                    status TEXT
                )
            """)

            cur.execute("""
                CREATE TEMP TABLE events (
                    user_id INTEGER,
                    event_type TEXT,
                    event_at TIMESTAMP
                )
            """)

            cur.execute("""
                INSERT INTO users (user_id, country)
                VALUES
                    (1, 'RU'),
                    (2, 'RU'),
                    (3, 'RU'),
                    (4, 'RU')
            """)

        yield conn


def get_predictions_data(conn):
    with conn.cursor() as cur:
        cur.execute(QUERY, (SNAPSHOT_DATE,))
        rows = cur.fetchall()

    return {row["user_id"]: row for row in rows}


# 1. Границы исторического окна
def test_history_boundaries(test_db):
    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO sessions
                (session_id, user_id, started_at, duration_seconds)
            VALUES
                (1, 1, '2026-05-01 23:59:59', 10),
                (2, 1, '2026-05-02 00:00:00', 60),
                (3, 1, '2026-06-30 23:59:59', 120),
                (4, 1, '2026-07-01 00:00:00', 999)
        """)

        cur.execute("""
            INSERT INTO events
                (user_id, event_type, event_at)
            VALUES
                (1, 'page_view', '2026-05-01 23:59:59'),
                (1, 'product_view', '2026-05-02 00:00:00'),
                (1, 'add_to_cart', '2026-06-30 23:59:59'),
                (1, 'checkout', '2026-07-01 00:00:00')
        """)

    data = get_predictions_data(test_db)
    user = data[1]

    assert user["sessions_last_60d"] == 2
    assert float(user["avg_session_duration_60d"]) == pytest.approx(60)

    assert user["events_last_60d"] == 2
    assert user["page_views_60d"] == 0
    assert user["product_views_60d"] == 1
    assert user["cart_additions_60d"] == 1
    assert user["checkouts_60d"] == 0

    assert data[2]["sessions_last_60d"] == 0
    assert data[2]["avg_session_duration_60d"] is None


@pytest.mark.parametrize(
    ("duration", "expected_average"),
    [(119, 89.5), (120, 90), (121, 60), (600, 60)]
)
def test_session_duration_is_known_at_snapshot(
    test_db, duration, expected_average
):
    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO sessions
                (session_id, user_id, started_at, duration_seconds)
            VALUES
                (10, 1, '2026-06-30 23:00:00', 60),
                (11, 1, '2026-06-30 23:58:00', %s),
                (12, 2, '2026-06-30 23:58:00', %s)
        """, (duration, duration))

    data = get_predictions_data(test_db)
    assert data[1]["sessions_last_60d"] == 2
    assert float(data[1]["avg_session_duration_60d"]) == pytest.approx(
        expected_average
    )
    assert data[2]["sessions_last_60d"] == 1
    if duration <= 120:
        assert float(data[2]["avg_session_duration_60d"]) == duration
    else:
        assert data[2]["avg_session_duration_60d"] is None


# 2. Границы целевого окна
def test_target_boundaries(test_db):
    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO orders
                (order_id, user_id, created_at, status)
            VALUES
                (1, 1, '2026-05-01 23:59:59', 'completed'),
                (2, 1, '2026-05-02 00:00:00', 'completed'),
                (3, 1, '2026-06-30 23:59:59', 'completed'),
                (4, 2, '2026-07-01 00:00:00', 'completed'),
                (5, 3, '2026-07-30 23:59:59', 'completed'),
                (6, 4, '2026-07-31 00:00:00', 'completed')
        """)

    data = get_predictions_data(test_db)

    assert data[1]["orders_last_60d"] == 2
    assert data[1]["target"] == 0

    assert data[2]["orders_last_60d"] == 0
    assert data[2]["target"] == 1

    assert data[3]["target"] == 1
    assert data[4]["target"] == 0


# 3. Будущие события не изменяют прошлые признаки
def test_future_events_do_not_change_features(test_db):
    before = get_predictions_data(test_db)[1]

    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO sessions
                (session_id, user_id, started_at, duration_seconds)
            VALUES
                (100, 1, '2026-07-05 12:00:00', 500)
        """)

        cur.execute("""
            INSERT INTO events
                (user_id, event_type, event_at)
            VALUES
                (1, 'page_view', '2026-07-05 12:00:00')
        """)

        cur.execute("""
            INSERT INTO orders
                (order_id, user_id, created_at, status)
            VALUES
                (100, 1, '2026-07-05 12:00:00', 'completed')
        """)

    after = get_predictions_data(test_db)[1]

    feature_columns = [
        "country",
        "orders_last_60d",
        "sessions_last_60d",
        "avg_session_duration_60d",
        "events_last_60d",
        "page_views_60d",
        "product_views_60d",
        "searches_60d",
        "cart_additions_60d",
        "checkouts_60d"
    ]

    for column in feature_columns:
        assert before[column] == after[column], (
            f"Признак {column} изменился из-за будущих событий"
        )

    assert before["target"] == 0
    assert after["target"] == 1


# 4. Только completed-заказы формируют target = 1
def test_only_completed_orders_are_positive(test_db):
    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO orders
                (order_id, user_id, created_at, status)
            VALUES
                (201, 1, '2026-07-10', 'completed'),
                (202, 2, '2026-07-10', 'cancelled'),
                (203, 3, '2026-07-10', 'refunded'),
                (204, 4, '2026-07-10', 'pending')
        """)

    data = get_predictions_data(test_db)

    assert data[1]["target"] == 1
    assert data[2]["target"] == 0
    assert data[3]["target"] == 0
    assert data[4]["target"] == 0

    # Добавляем успешный заказ пользователю,
    # у которого уже есть отменённый заказ.
    with test_db.cursor() as cur:
        cur.execute("""
            INSERT INTO orders
                (order_id, user_id, created_at, status)
            VALUES
                (205, 2, '2026-07-15', 'completed')
        """)

    data = get_predictions_data(test_db)

    assert data[2]["target"] == 1
    assert data[2]["orders_last_60d"] == 0
