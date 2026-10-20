from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

df = pd.read_csv(
    PROJECT_ROOT / "data" / "processed" / "dataset.csv",
    parse_dates=["snapshot_date"]
)


train_df = df[df["snapshot_date"] < pd.Timestamp("2026-08-01")]

X_train = train_df.drop(
    columns=["user_id", "target", "snapshot_date"]
)

y_train = train_df["target"]



PARAMS_PATH = PROJECT_ROOT / "config" / "best_params.json"

best_params = json.loads(
    PARAMS_PATH.read_text(encoding="utf-8")
)

cat_model = CatBoostClassifier(
    **best_params,
    iterations=400,
    loss_function="Logloss",
    random_seed=42,
    verbose=False,
    cat_features=["country"]
)
cat_model.fit(X_train, y_train)

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("Обучение CatBoost завершено")

cat_model.save_model(str(PROJECT_ROOT / "models" / "catboost_final.cbm"))

