
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset.csv"


@pytest.fixture
def dataset():
    return pd.read_csv(
        DATA_PATH,
        parse_dates=["snapshot_date"]
    )


# 1. Проверяем наличие обязательных столбцов
def test_required_columns(dataset):
    required_columns = {
        "user_id",
        "snapshot_date",
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
        "target"
    }

    assert required_columns.issubset(dataset.columns)


# 2. Проверяем отсутствие дубликатов
def test_no_duplicate_snapshots(dataset):
    duplicates = dataset.duplicated(
        subset=["user_id", "snapshot_date"]
    )

    assert duplicates.sum() == 0


# 3. Проверяем бинарность target
def test_target_values(dataset):
    assert dataset["target"].notna().all()
    assert dataset["target"].isin([0, 1]).all()


# 4. Проверяем неотрицательность счётчиков
def test_non_negative_counts(dataset):
    count_features = [
        "orders_last_60d",
        "sessions_last_60d",
        "events_last_60d",
        "page_views_60d",
        "product_views_60d",
        "searches_60d",
        "cart_additions_60d",
        "checkouts_60d"
    ]

    assert dataset[count_features].notna().all().all()
    assert (dataset[count_features] >= 0).all().all()
