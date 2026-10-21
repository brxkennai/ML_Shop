import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import average_precision_score


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset.csv"

VAL_DATES = [
    "2026-04-01",
    "2026-05-01",
    "2026-06-01",
    "2026-07-01",
]

CAT_FEATURES = ["country"]

PARAMS_PATH = PROJECT_ROOT / "config" / "best_params.json"


def load_dataset():
    return pd.read_csv(
        DATA_PATH,
        parse_dates=["snapshot_date"]
    )


def objective(trial, df):
    depth = trial.suggest_int("depth", 3, 7)

    learning_rate = trial.suggest_float(
        "learning_rate",
        0.01,
        0.1,
        log=True
    )

    fold_scores = []

    for val_date in VAL_DATES:
        date = pd.Timestamp(val_date)

        train_df = df[df["snapshot_date"] < date]
        val_df = df[df["snapshot_date"] == date]

        X_train = train_df.drop(
            columns=["user_id", "target", "snapshot_date"]
        )
        y_train = train_df["target"]

        X_val = val_df.drop(
            columns=["user_id", "target", "snapshot_date"]
        )
        y_val = val_df["target"]

        model = CatBoostClassifier(
            iterations=400,
            depth=depth,
            learning_rate=learning_rate,
            loss_function="Logloss",
            random_seed=42,
            verbose=False,
            cat_features=CAT_FEATURES
        )

        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_val)[:, 1]

        ap = average_precision_score(y_val, y_prob)
        fold_scores.append(ap)

    return float(np.mean(fold_scores))


def run_tuning(n_trials=10):
    if n_trials < 1:
        raise ValueError("n_trials должно быть положительным")

    df = load_dataset()

    sampler = optuna.samplers.TPESampler(seed=42)

    study = optuna.create_study(
        direction="maximize",
        sampler=sampler
    )

    study.optimize(
        lambda trial: objective(trial, df),
        n_trials=n_trials
    )

    # Replace the configuration only after a successful completed study.
    PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=PARAMS_PATH.parent,
            suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(study.best_params, temporary, indent=2)
            temporary.write("\n")
        temporary_path.replace(PARAMS_PATH)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print("\nЛучший средний AP:", study.best_value)
    print("Лучшие параметры:", study.best_params)
    print("Параметры сохранены:", PARAMS_PATH)

    return study


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run",
        action="store_true",
        help="Запустить подбор гиперпараметров"
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=10
    )

    args = parser.parse_args()

    if args.run:
        run_tuning(n_trials=args.trials)
    else:
        best_params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
        print("Сохранённые лучшие параметры:", best_params)
        print("Подбор Optuna не запущен.")
        print("Для повторного подбора используйте --run")
