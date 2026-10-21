from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "catboost_final.cbm"


def main():
    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))
    df = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "dataset.csv",
        parse_dates=["snapshot_date"]
    )
    sample = df[df["snapshot_date"] == pd.Timestamp("2026-08-01")].copy()
    sample["purchase_probability"] = model.predict_proba(
        sample[model.feature_names_]
    )[:, 1]
    predictions = sample[
        ["user_id", "snapshot_date", "purchase_probability"]
    ].sort_values(by="purchase_probability", ascending=False)
    output_dir = PROJECT_ROOT / "data" / "predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_dir / "august_predictions.csv", index=False)
    print("Прогнозы сохранены!")
    print("Количество пользователей:", len(predictions))
    print(predictions.head(10))


if __name__ == "__main__":
    main()
