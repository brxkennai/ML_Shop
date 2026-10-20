
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier

from evaluate import calculate_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset.csv"
MODEL_PATH = PROJECT_ROOT / "models" / "catboost_final.cbm"


def main():
    df = pd.read_csv(
        DATA_PATH,
        parse_dates=["snapshot_date"]
    )

    test_df = df[
        df["snapshot_date"] == pd.Timestamp("2026-08-01")
    ].copy()

    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))

    X_test = test_df[model.feature_names_]
    y_test = test_df["target"]

    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = calculate_metrics(
        y_true=y_test,
        y_prob=y_prob,
        k=100
    )

    print("Оценка модели на августе 2026")
    print("-" * 40)
    print("Количество пользователей:", len(test_df))
    print("Успешных покупателей:", int(y_test.sum()))
    print("Доля положительного класса:", round(y_test.mean(), 4))

    print("\nМетрики:")
    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")


if __name__ == "__main__":
    main()
