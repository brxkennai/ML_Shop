import importlib
import sys

import catboost
import dotenv
import pandas as pd
import psycopg
import pytest


@pytest.mark.parametrize("module", ["src.train", "src.predict", "src.check_connection"])
def test_import_does_not_run_pipeline(module, monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Import must not run the pipeline")

    monkeypatch.setattr(pd, "read_csv", unexpected)
    monkeypatch.setattr(catboost, "CatBoostClassifier", unexpected)
    monkeypatch.setattr(psycopg, "connect", unexpected)
    monkeypatch.setattr(dotenv, "load_dotenv", unexpected)
    monkeypatch.delitem(sys.modules, module, raising=False)
    try:
        imported = importlib.import_module(module)
        assert callable(imported.main)
    finally:
        sys.modules.pop(module, None)
