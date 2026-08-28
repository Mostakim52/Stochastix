import pandas as pd
import pytest
import yaml
from fastapi.testclient import TestClient

from stockforge.api.app import app

TICKERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from stockforge.config import AppConfig
    from stockforge.data.synthetic import generate_synthetic_panel
    from stockforge.forecasting import generate_forecasts, persist_forecasts
    from stockforge.training import train_all

    tmp = tmp_path_factory.mktemp("api")
    config = AppConfig()
    config.universe.tickers = list(TICKERS)
    config.artifacts_dir = str(tmp / "artifacts")
    config.data.cache_dir = str(tmp / "cache")
    config.features.horizons = [1]
    config.cv.n_splits = 2
    config.cv.min_train_days = 420
    config.cv.embargo_days = 20
    config.model.lightgbm.n_estimators = 60

    config_path = tmp / "config.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump()), encoding="utf-8")

    import os

    old = os.environ.get("STOCKFORGE_CONFIG")
    os.environ["STOCKFORGE_CONFIG"] = str(config_path)
    try:
        panel = generate_synthetic_panel(TICKERS, periods=900, seed=11)
        cache_dir = tmp / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        from stockforge.data.panel import FIELDS

        for ticker in TICKERS:
            frame = pd.DataFrame({f: getattr(panel, f)[ticker] for f in FIELDS})
            frame.to_parquet(cache_dir / f"{ticker}.parquet")
        train_all(panel, config)
        tables = generate_forecasts(panel, config)
        persist_forecasts(tables, config)

        with TestClient(app) as c:
            yield c
    finally:
        if old is None:
            os.environ.pop("STOCKFORGE_CONFIG", None)
        else:
            os.environ["STOCKFORGE_CONFIG"] = old


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["latest_run"] is not None


def test_tickers(client):
    response = client.get("/api/tickers")
    assert response.status_code == 200
    assert response.json()["tickers"] == TICKERS


def test_forecast_endpoint(client):
    response = client.get("/api/forecast/1")
    assert response.status_code == 200
    body = response.json()
    assert body["horizon_days"] == 1
    tickers_returned = {f["ticker"] for f in body["forecasts"]}
    assert tickers_returned == set(TICKERS)
    for record in body["forecasts"]:
        assert record["direction"] in {"up", "down", "flat"}
        assert record["predicted_price"] > 0


def test_forecast_unknown_horizon_404(client):
    response = client.get("/api/forecast/999")
    assert response.status_code == 404


def test_portfolio_endpoint(client):
    response = client.post(
        "/api/portfolio", json={"capital": 50_000, "schemes": ["max_sharpe", "hrp", "equal_weight"]}
    )
    assert response.status_code == 200
    allocations = response.json()["allocations"]
    assert len(allocations) == 3
    for alloc in allocations:
        weights = alloc["weights"]
        assert abs(sum(weights.values()) - 1.0) < 1e-4
        dollars = sum(alloc["dollar_allocation"].values())
        assert dollars == pytest.approx(50_000, rel=1e-3)


def test_portfolio_unknown_scheme_400(client):
    response = client.post("/api/portfolio", json={"schemes": ["nope"]})
    assert response.status_code == 400


def test_retrain_background(client):
    response = client.post("/api/retrain", json={"synthetic": True})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
