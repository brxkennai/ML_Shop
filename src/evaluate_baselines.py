"""Compare reproducible baselines on the same historical August holdout."""
from pathlib import Path
import json

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from .evaluate import calculate_metrics
except ImportError:
    from evaluate import calculate_metrics


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def evaluate_baselines():
    df = pd.read_csv(
        PROJECT_ROOT / "data" / "processed" / "dataset.csv",
        parse_dates=["snapshot_date"]
    )
    cutoff = pd.Timestamp("2026-08-01")
    train = df[df["snapshot_date"] < cutoff]
    test = df[df["snapshot_date"] == cutoff]
    feature_columns = df.columns.drop(["user_id", "target", "snapshot_date"])
    numeric_columns = feature_columns.drop("country")
    preprocess = ColumnTransformer([
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler())
        ]), numeric_columns),
        ("country", OneHotEncoder(handle_unknown="ignore"), ["country"])
    ])
    models = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": Pipeline([
            ("preprocess", preprocess),
            ("model", LogisticRegression(max_iter=1000, random_state=42))
        ])
    }
    results = {}
    for name, model in models.items():
        model.fit(train[feature_columns], train["target"])
        probability = model.predict_proba(test[feature_columns])[:, 1]
        metrics = calculate_metrics(test["target"], probability, k=100)
        # A constant score cannot rank users; top-k metrics depend on tie order.
        if name == "dummy":
            metrics["precision_at_k"] = None
            metrics["lift_at_k"] = None
        results[name] = metrics
    return results


if __name__ == "__main__":
    print(json.dumps(evaluate_baselines(), indent=2))
