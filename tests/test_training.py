from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from stockforge.config import AppConfig
from stockforge.data.synthetic import generate_synthetic_panel
from stockforge.forecasting import generate_forecasts, persist_forecasts
from stockforge.models.base import ReturnModel, load_json
from stockforge.models.registry import ModelRegistry
from stockforge.training import train_all

TICKERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("train")
    panel = generate_synthetic_panel(TICKERS, periods=900, seed=3)
    config = AppConfig()
    config.universe.tickers = list(TICKERS)
    config.artifacts_dir = str(tmp / "artifacts")
    config.features.horizons = [1]
    config.cv.n_splits = 2
    config.cv.min_train_days = 420
    config.cv.embargo_days = 20
    config.model.lightgbm.n_estimators = 60
    outcome = train_all(panel, config)
    return panel, config, outcome


def test_train_creates_complete_run(trained):
    _panel, config, outcome = trained
    run_dir = Path(outcome.run_dir)
    assert (run_dir / "model_h1.joblib").exists()
    assert (run_dir / "predictions_h1.parquet").exists()
    metadata = load_json(run_dir / "metadata.json")
    assert "1" in metadata["per_horizon"]
    block = metadata["per_horizon"]["1"]
    assert block["best_model"] in {"naive", "drift", "elasticnet", "lightgbm", "ensemble"}
    assert block["n_obs"] > 300
    assert len(metadata["feature_names"]) == 17


def test_predictions_wide_format(trained):
    _panel, _config, outcome = trained
    preds = pd.read_parquet(Path(outcome.run_dir) / "predictions_h1.parquet")
    assert list(preds.columns) == TICKERS
    assert preds.notna().any().any()


def test_registry_latest(trained):
    _panel, config, outcome = trained
    entry = ModelRegistry(Path(config.artifacts_dir) / "models").latest()
    assert entry.run_id == outcome.run_id
    model = ReturnModel.load(entry.model_file(1))
    assert isinstance(model, ReturnModel)


def test_forecast_generation(trained):
    panel, config, _outcome = trained
    tables = generate_forecasts(panel, config)
    assert set(tables) == {1}
    frame = tables[1].frame
    price_cols = [c for c in frame.columns if c.startswith("predicted_price")]
    assert price_cols
    assert set(frame.index) <= set(TICKERS)
    assert frame["direction"].isin(["up", "down", "flat"]).all()
    assert (frame[price_cols[0]] > 0).all()


def test_persist_forecasts(trained):
    panel, config, _outcome = trained
    tables = generate_forecasts(panel, config)
    target = persist_forecasts(tables, config)
    assert Path(target).exists()
    assert (Path(config.artifacts_dir) / "forecasts" / "latest.parquet").exists()
