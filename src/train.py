import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PARAMS_PATH = PROJECT_ROOT / "config" / "best_params.json"


def main():
    df = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "dataset.csv",
        parse_dates=["snapshot_date"]
    )
    train_df = df[df["snapshot_date"] < pd.Timestamp("2026-08-01")]
    X_train = train_df.drop(columns=["user_id", "target", "snapshot_date"])
    y_train = train_df["target"]
    best_params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    cat_model = CatBoostClassifier(
        **best_params,
        iterations=400,
        loss_function="Logloss",
        random_seed=42,
        verbose=False,
        cat_features=["country"]
    )
    cat_model.fit(X_train, y_train)
    model_path = PROJECT_ROOT / "models" / "catboost_final.cbm"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    cat_model.save_model(str(model_path))
    print("X_train:", X_train.shape)
    print("y_train:", y_train.shape)
    print("Обучение CatBoost завершено")


if __name__ == "__main__":
    main()
