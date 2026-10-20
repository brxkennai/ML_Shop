
import numpy as np
import pytest

from src.evaluate import calculate_metrics


def test_perfect_ranking():
    y_true = np.array([0, 1, 0, 1, 0])
    y_prob = np.array([0.2, 0.9, 0.6, 0.8, 0.1])

    metrics = calculate_metrics(y_true, y_prob, k=2)

    assert metrics["roc_auc"] == pytest.approx(1.0)
    assert metrics["ap"] == pytest.approx(1.0)
    assert metrics["precision_at_k"] == pytest.approx(1.0)
    assert metrics["lift_at_k"] == pytest.approx(2.5)



def test_invalid_k():
    y_true = np.array([0, 1, 0, 1, 0])
    y_prob = np.array([0.2, 0.9, 0.6, 0.8, 0.1])

    with pytest.raises(ValueError):
        calculate_metrics(y_true, y_prob, k=10)


def test_different_lengths():
    y_true = np.array([0, 1, 0, 1, 0])
    y_prob = np.array([0.2, 0.9, 0.6])

    with pytest.raises(ValueError):
        calculate_metrics(y_true, y_prob)


def test_invalid_probabilities():
    y_true = np.array([0, 1, 0, 1, 0])
    y_prob = np.array([0.2, 1.5, 0.6, 0.8, 0.1])

    with pytest.raises(ValueError):
        calculate_metrics(y_true, y_prob)
