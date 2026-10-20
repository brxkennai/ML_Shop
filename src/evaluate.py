import numpy as np

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score
)


def calculate_metrics(y_true, y_prob, k=100):
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if y_true.ndim != 1 or y_prob.ndim != 1:
        raise ValueError("y_true и y_prob должны быть одномерными")

    if len(y_true) != len(y_prob):
        raise ValueError("Количество меток и вероятностей не совпадает")

    if not 1 <= k <= len(y_true):
        raise ValueError("k должно быть от 1 до числа наблюдений")

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("y_true должен содержать только 0 и 1")

    if not np.isfinite(y_prob).all() or not ((0 <= y_prob) & (y_prob <= 1)).all():
        raise ValueError("Вероятности должны быть числами от 0 до 1")

    if len(np.unique(y_true)) < 2:
        raise ValueError("Для ROC-AUC нужны оба класса: 0 и 1")

    roc_auc = roc_auc_score(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)
    top_indices = np.argsort(y_prob)[-k:]

    precision_at_k = y_true[top_indices].mean()

    baseline = y_true.mean()

    lift_at_k = precision_at_k / baseline

    return {
        "roc_auc": float(roc_auc),
        "ap": float(ap),
        "precision_at_k": float(precision_at_k),
        "lift_at_k": float(lift_at_k)
    }