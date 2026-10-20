
from pathlib import Path
from catboost import CatBoostClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "catboost_final.cbm"

model = CatBoostClassifier()
model.load_model(str(MODEL_PATH))


import pandas as pd

df = pd.read_csv(
    PROJECT_ROOT / "data" / "processed" / "dataset.csv",
    parse_dates=["snapshot_date"]
)

sample = df[
    df["snapshot_date"] == pd.Timestamp("2026-08-01")
].copy()

X_new = sample[model.feature_names_]

model.predict_proba(X_new)
probabilities = model.predict_proba(X_new)[:, 1]

sample["purchase_probability"] = probabilities

output_dir = PROJECT_ROOT / "data" / "predictions"
output_dir.mkdir(parents=True, exist_ok=True)

predictions = sample[
    ["user_id", "snapshot_date", "purchase_probability"]
].copy()

predictions = predictions.sort_values(
    by="purchase_probability",
    ascending=False
)

predictions.to_csv(
    output_dir / "august_predictions.csv",
    index=False
)

print("Прогнозы сохранены!")
print("Количество пользователей:", len(predictions))
print(predictions.head(10))


