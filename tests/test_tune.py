import json

import pytest

from src import tune


def test_tuning_saves_best_params_for_training(tmp_path, monkeypatch):
    params_path = tmp_path / "config" / "best_params.json"
    monkeypatch.setattr(tune, "PARAMS_PATH", params_path)
    monkeypatch.setattr(tune, "load_dataset", lambda: None)

    def objective(trial, dataset):
        trial.suggest_int("depth", 3, 3)
        trial.suggest_float("learning_rate", 0.05, 0.05)
        return 0.25

    monkeypatch.setattr(tune, "objective", objective)
    study = tune.run_tuning(n_trials=1)

    assert json.loads(params_path.read_text(encoding="utf-8")) == study.best_params
    assert study.best_value == pytest.approx(0.25)
    assert not list(params_path.parent.glob("*.tmp"))


def test_failed_tuning_preserves_previous_params(tmp_path, monkeypatch):
    params_path = tmp_path / "best_params.json"
    previous = '{"depth": 4, "learning_rate": 0.03}\n'
    params_path.write_text(previous, encoding="utf-8")
    monkeypatch.setattr(tune, "PARAMS_PATH", params_path)
    monkeypatch.setattr(tune, "load_dataset", lambda: None)

    def objective(trial, dataset):
        raise RuntimeError("training failed")

    monkeypatch.setattr(tune, "objective", objective)
    with pytest.raises(RuntimeError, match="training failed"):
        tune.run_tuning(n_trials=1)

    assert params_path.read_text(encoding="utf-8") == previous


def test_tuning_rejects_zero_trials(monkeypatch):
    monkeypatch.setattr(tune, "load_dataset", lambda: None)
    with pytest.raises(ValueError, match="n_trials"):
        tune.run_tuning(n_trials=0)
