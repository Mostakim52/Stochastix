"""FastAPI application exposing forecasts, portfolios, health and retraining."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from stockforge import __version__
from stockforge.api.schemas import (
    ForecastRecord,
    ForecastResponse,
    HealthResponse,
    PortfolioAllocation,
    PortfolioRequest,
    PortfolioResponse,
    RetrainRequest,
    TaskAccepted,
    TickerResponse,
)
from stockforge.config import AppConfig, load_config
from stockforge.data.panel import PricePanel
from stockforge.exceptions import RegistryError
from stockforge.log import configure, get_logger
from stockforge.models.registry import ModelRegistry
from stockforge.portfolio.optimizer import SCHEMES, PortfolioOptimizer, shrunk_covariance

logger = get_logger("api")

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure(os.environ.get("STOCKFORGE_LOG_LEVEL", "INFO"))
    app.state.config = load_config(os.environ.get("STOCKFORGE_CONFIG"))
    logger.info("Stochastix API ready")
    yield


app = FastAPI(
    title="Stochastix API",
    description="ML stock forecasts and Black-Litterman portfolio optimization.",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health")
async def health_root() -> dict:
    """Liveness probe for platform health checks (Render, Fly.io, Docker)."""
    return {"status": "ok", "version": __version__}


# Serve frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def root():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/dashboard")
    async def dashboard_redirect():
        return FileResponse(FRONTEND_DIR / "index.html")


# API router with /api prefix
api_router = APIRouter(prefix="/api")


def _config() -> AppConfig:
    return app.state.config  # type: ignore[attr-defined]


def _registry() -> ModelRegistry:
    return ModelRegistry(Path(_config().artifacts_dir) / "models")


def _cached_forecasts() -> tuple[dict[int, pd.DataFrame], str]:
    path = Path(_config().artifacts_dir) / "forecasts" / "latest.parquet"
    if not path.exists():
        raise HTTPException(404, "No forecasts yet. Run `stochastix forecast` first.")
    try:
        raw = pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001 - reader/writer mismatches etc.
        raise HTTPException(
            503, f"Forecast artifact unreadable ({exc}). Rerun `stochastix forecast`."
        ) from exc
    tables = {int(h): sub.droplevel("horizon") for h, sub in raw.groupby(level="horizon")}
    run = "latest"
    try:
        run = _registry().latest().run_id
    except RegistryError:
        pass
    return tables, run


def _panel_or_raise() -> PricePanel:
    config = _config()
    cache_dir = Path(config.data.cache_dir)
    try:
        from stockforge.data.ingestion import load_panel_from_cache

        return load_panel_from_cache(config.universe.tickers, cache_dir)
    except FileNotFoundError as exc:
        raise HTTPException(
            404, f"No cached market data ({exc}). Run `stochastix ingest` first."
        ) from exc


@api_router.get("/prices")
def prices(days: int = 252) -> dict:
    """Return close prices for the last N trading days."""
    panel = _panel_or_raise()
    df = panel.close.tail(days)
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in df.index],
        "tickers": {
            col: [round(float(v), 2) if np.isfinite(v) else None for v in df[col]]
            for col in df.columns
        },
    }


@api_router.get("/correlations")
def correlations(days: int = 120) -> dict:
    """Return correlation matrix of daily returns."""
    panel = _panel_or_raise()
    rets = panel.simple_returns().tail(days).dropna(how="all")
    corr = rets.corr()
    tickers = list(corr.columns)
    n = len(tickers)
    matrix = [[round(float(corr.iloc[i, j]), 4) for j in range(n)] for i in range(n)]
    return {"tickers": tickers, "matrix": matrix, "days": days}


@api_router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    run_id = None
    try:
        run_id = _registry().latest().run_id
    except RegistryError:
        pass
    return HealthResponse(status="ok", version=__version__, latest_run=run_id)


@api_router.get("/tickers", response_model=TickerResponse)
def tickers() -> TickerResponse:
    cfg = _config()
    return TickerResponse(tickers=cfg.universe.tickers, benchmark=cfg.universe.benchmark)


@api_router.get("/forecast/{horizon}", response_model=ForecastResponse)
def forecast(horizon: int) -> ForecastResponse:
    tables, run_id = _cached_forecasts()
    if horizon not in tables:
        available = ", ".join(str(h) for h in sorted(tables))
        raise HTTPException(404, f"Horizon {horizon}d unavailable; trained horizons: {available}")
    frame = tables[horizon]
    price_col = next((c for c in frame.columns if c.startswith("predicted_price")), None)
    records = []
    for ticker, row in frame.iterrows():
        records.append(
            ForecastRecord(
                ticker=str(ticker),
                last_close=_safe(row.get("last_close")),
                predicted_price=_safe(row.get(price_col)) if price_col else None,
                expected_return_pct=_safe(row.get("expected_return_pct")),
                direction=row.get("direction"),
            )
        )
    as_of = Path(_config().artifacts_dir) / "forecasts" / "latest.json"
    as_of_str = str(frame.index.name or "")
    if as_of.exists():
        import json

        payload = json.loads(as_of.read_text(encoding="utf-8"))
        as_of_str = payload.get(str(horizon), {}).get("as_of", as_of_str)
    return ForecastResponse(
        horizon_days=horizon, as_of=as_of_str, model_run=run_id, forecasts=records
    )


@api_router.post("/portfolio", response_model=PortfolioResponse)
def portfolio(request: PortfolioRequest) -> PortfolioResponse:
    tables, _ = _cached_forecasts()
    horizon = max(tables.keys())
    frame = tables[horizon]

    preds = frame["predicted_log_return"]
    mu_model = ((np.exp(preds.clip(-2, 2) / horizon * 252.0)) - 1.0).clip(-0.95, 3.0)

    panel = _panel_or_raise()
    returns = panel.simple_returns().tail(_config().portfolio.lookback_days)
    cov = shrunk_covariance(returns) * 252.0

    if request.black_litterman:
        from stockforge.portfolio.blacklitterman import black_litterman, equilibrium_weights

        w_eq = equilibrium_weights(tickers=list(mu_model.index))
        mu, _ = black_litterman(cov, w_eq, mu_model, delta=_config().portfolio.delta)
        mu = mu.reindex(mu_model.index).clip(-0.95, 3.0)
    else:
        hist_mu = (returns.mean() * 252.0).reindex(mu_model.index).fillna(0.0).clip(-0.95, 3.0)
        blend = _config().portfolio.blend_model_weight
        mu = (1.0 - blend) * hist_mu + blend * mu_model

    optimizer = PortfolioOptimizer(
        mu,
        cov,
        risk_free_rate=_config().portfolio.risk_free_rate,
        max_weight=_config().portfolio.max_weight,
    )
    allocations = []
    for scheme in request.schemes:
        if scheme not in SCHEMES:
            raise HTTPException(400, f"Unknown scheme '{scheme}'. Available: {sorted(SCHEMES)}")
        result = SCHEMES[scheme](optimizer, cov)
        weights = {k: round(float(v), 6) for k, v in result.weights.items()}
        allocations.append(
            PortfolioAllocation(
                scheme=scheme,
                weights=weights,
                dollar_allocation={k: round(v * request.capital, 2) for k, v in weights.items()},
                exp_return=result.exp_return,
                exp_vol=result.exp_vol,
                sharpe=result.sharpe,
            )
        )
    as_of = str(frame.index.name) if frame.index.name else ""
    meta_json = Path(_config().artifacts_dir) / "forecasts" / "latest.json"
    if meta_json.exists():
        import json

        payload = json.loads(meta_json.read_text(encoding="utf-8"))
        as_of = payload.get(str(horizon), {}).get("as_of", as_of)
    return PortfolioResponse(as_of=as_of, capital=request.capital, allocations=allocations)


@api_router.post("/retrain", response_model=TaskAccepted)
def retrain(
    request: RetrainRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(default=None),
) -> TaskAccepted:
    expected = os.environ.get("STOCKFORGE_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(401, "Invalid or missing X-API-Key")
    background_tasks.add_task(_run_retrain, request.synthetic)
    return TaskAccepted(status="accepted", detail="retraining started in background")


app.include_router(api_router)


def _run_retrain(synthetic: bool) -> None:
    from stockforge.data.synthetic import generate_synthetic_panel
    from stockforge.training import train_all

    config = _config()
    if synthetic:
        panel = generate_synthetic_panel(config.universe.tickers)
    else:
        from stockforge.data.ingestion import download_panel

        panel = download_panel(
            config.universe.tickers,
            start=config.data.start,
            cache_dir=config.data.cache_dir,
            refresh=True,
            retry_attempts=config.data.retry_attempts,
            backoff_seconds=config.data.retry_backoff_seconds,
        )
    outcome = train_all(panel, config)
    logger.info("background retrain complete: %s", outcome.run_id)


def _safe(value) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if np.isfinite(numeric) else None
