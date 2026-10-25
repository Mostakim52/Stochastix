"""Stochastix command line interface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from stockforge import __version__
from stockforge.config import AppConfig, load_config
from stockforge.data.panel import PricePanel
from stockforge.data.validation import validate_panel
from stockforge.log import configure, get_logger
from stockforge.models.base import dump_json
from stockforge.models.registry import ModelRegistry
from stockforge.portfolio.optimizer import (
    SCHEMES,
    PortfolioOptimizer,
    PortfolioResult,
    shrunk_covariance,
)

app = typer.Typer(
    name="stochastix", help="AI stock forecasting & portfolio optimization.", no_args_is_help=True
)
console = Console()
logger = get_logger("cli")

DEFAULT_SCHEMES = "max_sharpe,min_variance,risk_parity,hrp,equal_weight"


def _plain_str(value: object, fallback: str) -> str:
    """Typer leaves OptionInfo objects as defaults when commands call each other."""
    return value if isinstance(value, str) else fallback


def _cfg(config_path: str | None) -> AppConfig:
    config = load_config(config_path)
    configure(config.log_level)
    return config


def _resolve_panel(config: AppConfig, synthetic: bool, refresh: bool = False) -> PricePanel:
    if synthetic:
        from stockforge.data.synthetic import generate_synthetic_panel

        logger.info("using SYNTHETIC market data (offline demo mode)")
        return generate_synthetic_panel(config.universe.tickers)
    from stockforge.data.ingestion import download_panel

    return download_panel(
        config.universe.tickers,
        start=config.data.start,
        cache_dir=config.data.cache_dir,
        refresh=refresh,
        retry_attempts=config.data.retry_attempts,
        backoff_seconds=config.data.retry_backoff_seconds,
    )


def _print_weights(results: dict[str, PortfolioResult], capital: float) -> None:
    for scheme, result in results.items():
        stats = (
            f"exp ret {result.exp_return:+.1%}, vol {result.exp_vol:.1%}, "
            f"sharpe {result.sharpe:.2f}"
        )
        table = Table(title=f"{scheme}  ({stats})")
        table.add_column("Ticker")
        table.add_column("Weight", justify="right")
        table.add_column(f"Allocation (${capital:,.0f})", justify="right")
        for ticker, weight in (
            result.weights[result.weights > 1e-4].sort_values(ascending=False).items()
        ):
            table.add_row(ticker, f"{weight:.2%}", f"${weight * capital:,.0f}")
        console.print(table)


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"stochastix {__version__}")


@app.command()
def ingest(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(
        False, "--synthetic", help="Generate offline synthetic data instead of hitting yfinance"
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the parquet cache"),
) -> None:
    """Download price history into the local cache and validate it."""
    config = _cfg(config_path)
    panel = _resolve_panel(config, synthetic, refresh)
    issues = validate_panel(panel)
    table = Table(title="Ingested market data")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Tickers", ", ".join(panel.tickers))
    table.add_row("Rows", f"{len(panel.dates)}")
    table.add_row("Range", f"{panel.dates.min().date()} - {panel.dates.max().date()}")
    table.add_row("Issues", "; ".join(issues) if issues else "none")
    console.print(table)


@app.command()
def train(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(False, "--synthetic/--no-synthetic"),
    quick: bool = typer.Option(False, "--quick", help="Shrink model/CV sizes for smoke tests"),
) -> None:
    """Run walk-forward training across all horizons and store a registry run."""
    from stockforge.training import train_all

    config = _cfg(config_path)
    if quick:
        config.model.lightgbm.n_estimators = 120
        config.cv.n_splits = 3
    panel = _resolve_panel(config, synthetic)
    outcome = train_all(panel, config)
    for horizon_key, block in outcome.metadata["per_horizon"].items():
        console.print(
            f"[bold]h={horizon_key}[/] best=[cyan]{block['best_model']}[/] "
            f"rmse={block['pooled_rmse'][block['best_model']]:.5f} "
            f"resid_std={block['residual_std']:.5f}"
        )
    console.print(f"[green]run saved:[/] {outcome.run_dir}")


@app.command()
def forecast(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(False, "--synthetic/--no-synthetic"),
) -> None:
    """Produce price forecasts from the latest trained run."""
    from stockforge.forecasting import generate_forecasts, persist_forecasts

    config = _cfg(config_path)
    panel = _resolve_panel(config, synthetic)
    tables = generate_forecasts(panel, config)
    target = persist_forecasts(tables, config)
    for horizon, table_frame in sorted(tables.items()):
        rich_table = Table(title=f"{horizon}-day forecasts as of {table_frame.as_of.date()}")
        for col in ["Ticker", "Last close", "Forecast", "Exp. return", "Direction"]:
            rich_table.add_column(col, justify="right" if col != "Ticker" else "left")
        frame = table_frame.frame
        price_col = next(c for c in frame.columns if c.startswith("predicted_price"))
        for ticker, row in frame.iterrows():
            rich_table.add_row(
                ticker,
                f"${row['last_close']:,.2f}",
                f"${row[price_col]:,.2f}",
                f"{row['expected_return_pct']:+.2f}%",
                str(row["direction"]),
            )
        console.print(rich_table)
    console.print(f"[green]saved:[/] {target}")


@app.command()
def optimize(
    capital: float = typer.Option(100_000.0, "--capital"),
    schemes: str | None = typer.Option(
        None, "--schemes", help="Comma-separated schemes; default covers all core ones"
    ),
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(False, "--synthetic/--no-synthetic"),
    pure_model: bool = typer.Option(
        False, "--pure-model", help="Skip blending with historical means"
    ),
) -> None:
    """Optimize portfolios around model forecasts."""
    from stockforge.forecasting import generate_forecasts, persist_forecasts

    config = _cfg(config_path)
    panel = _resolve_panel(config, synthetic)
    tables = generate_forecasts(panel, config)
    persist_forecasts(tables, config)

    horizon = max(tables.keys())
    frame = tables[horizon].frame
    preds = frame["predicted_log_return"]
    mu_model = ((np.exp(preds.clip(-2, 2) / horizon * 252.0)) - 1.0).clip(-0.95, 3.0)

    returns = panel.simple_returns().tail(config.portfolio.lookback_days)
    cov = shrunk_covariance(returns) * 252.0
    hist_mu = (returns.mean() * 252.0).clip(-0.95, 3.0).reindex(mu_model.index).fillna(0.0)
    blend_w = 0.0 if pure_model else config.portfolio.blend_model_weight
    mu = (1.0 - blend_w) * hist_mu + blend_w * mu_model

    optimizer = PortfolioOptimizer(
        mu,
        cov,
        risk_free_rate=config.portfolio.risk_free_rate,
        max_weight=config.portfolio.max_weight,
    )
    selected = [s.strip() for s in _plain_str(schemes, DEFAULT_SCHEMES).split(",") if s.strip()]
    results = {scheme: SCHEMES[scheme](optimizer, cov) for scheme in selected}
    _print_weights(results, capital)

    out_dir = Path(config.artifacts_dir) / "portfolios"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "as_of": str(tables[horizon].as_of.date()),
        "horizon_days": horizon,
        "capital": capital,
        "schemes": {
            scheme: {
                "weights": {k: round(float(v), 6) for k, v in res.weights.items()},
                "exp_return": res.exp_return,
                "exp_vol": res.exp_vol,
                "sharpe": res.sharpe,
            }
            for scheme, res in results.items()
        },
    }
    dump_json(payload, out_dir / "latest.json")
    console.print(f"[green]saved:[/] {out_dir / 'latest.json'}")


@app.command()
def backtest(
    schemes: str | None = typer.Option(
        None,
        "--schemes",
        help="Comma-separated schemes; default max_sharpe,min_variance,hrp,equal_weight",
    ),
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(False, "--synthetic/--no-synthetic"),
    black_litterman: bool = typer.Option(False, "--black-litterman"),
) -> None:
    """Backtest strategies on strictly out-of-sample predictions."""
    from stockforge.backtest.engine import WalkForwardBacktester

    config = _cfg(config_path)
    panel = _resolve_panel(config, synthetic)
    entry = ModelRegistry(Path(config.artifacts_dir) / "models").latest()

    horizon = max(int(h) for h in entry.metadata.get("horizons", [5]))
    pred_path = entry.prediction_file(horizon)
    predictions = pd.read_parquet(pred_path)

    tester = WalkForwardBacktester(
        panel,
        predictions,
        horizon=horizon,
        rebalance_days=config.backtest.rebalance_days,
        cost_bps=config.backtest.cost_bps,
        lookback_days=config.portfolio.lookback_days,
        risk_free_rate=config.portfolio.risk_free_rate,
        max_weight=config.portfolio.max_weight,
        initial_capital=config.backtest.initial_capital,
    )
    selected = [
        s.strip()
        for s in _plain_str(schemes, "max_sharpe,min_variance,hrp,equal_weight").split(",")
        if s.strip()
    ]
    results = {}
    for scheme in selected:
        results[scheme] = tester.run(scheme, black_litterman_views=black_litterman)

    metrics_table = Table(title=f"Walk-forward backtest (h={horizon}d OOS predictions)")
    for col in ["Scheme", "CAGR", "Vol", "Sharpe", "MaxDD", "Calmar", "Excess CAGR"]:
        metrics_table.add_column(col, justify="right" if col != "Scheme" else "left")
    for scheme, res in results.items():
        m = res.metrics
        metrics_table.add_row(
            scheme,
            f"{m['cagr']:+.2%}",
            f"{m['volatility']:.2%}",
            f"{m['sharpe']:.2f}",
            f"{m['max_drawdown']:.1%}",
            f"{m['calmar']:.2f}",
            f"{m['excess_cagr']:+.2%}",
        )
    console.print(metrics_table)

    out_dir = Path(config.artifacts_dir) / "backtest"
    out_dir.mkdir(parents=True, exist_ok=True)
    equity_frame = pd.concat({s: r.equity for s, r in results.items()}, axis=1)
    equity_frame.to_csv(out_dir / "equity.csv")
    bench = pd.DataFrame({"benchmark_equal_weight": results[selected[0]].benchmark_equity})
    bench.to_csv(out_dir / "benchmark.csv")
    payload = {
        scheme: {
            k: (v if isinstance(v, float) and np.isfinite(v) else None)
            for k, v in res.metrics.items()
        }
        for scheme, res in results.items()
    }
    dump_json(payload, out_dir / "metrics.json")
    console.print(f"[green]saved:[/] {out_dir}")


@app.command()
def report(
    capital: float = typer.Option(100_000.0, "--capital"),
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(False, "--synthetic/--no-synthetic"),
) -> None:
    """Render a full markdown research report from fresh inference."""
    from stockforge.backtest.engine import WalkForwardBacktester
    from stockforge.forecasting import generate_forecasts, persist_forecasts
    from stockforge.reporting.report import render_markdown_report, save_report

    config = _cfg(config_path)
    panel = _resolve_panel(config, synthetic)
    entry = ModelRegistry(Path(config.artifacts_dir) / "models").latest()
    metadata = dict(entry.metadata)
    metadata["run_id"] = entry.run_id

    tables = generate_forecasts(panel, config)
    persist_forecasts(tables, config)
    horizon = max(tables.keys())

    returns = panel.simple_returns().tail(config.portfolio.lookback_days)
    cov = shrunk_covariance(returns) * 252.0
    preds = tables[horizon].frame["predicted_log_return"]
    mu = ((np.exp(preds.clip(-2, 2) / horizon * 252.0)) - 1.0).clip(-0.95, 3.0)
    optimizer = PortfolioOptimizer(
        mu,
        cov,
        risk_free_rate=config.portfolio.risk_free_rate,
        max_weight=config.portfolio.max_weight,
    )
    portfolios = {
        "max_sharpe": SCHEMES["max_sharpe"](optimizer, cov),
        "min_variance": SCHEMES["min_variance"](optimizer, cov),
        "hrp": SCHEMES["hrp"](optimizer, cov),
        "risk_parity": SCHEMES["risk_parity"](optimizer, cov),
    }

    backtests = {}
    try:
        oos_h = max(int(h) for h in entry.metadata.get("horizons", [horizon]))
        tester = WalkForwardBacktester(
            panel,
            pd.read_parquet(entry.prediction_file(oos_h)),
            horizon=oos_h,
            rebalance_days=config.backtest.rebalance_days,
            cost_bps=config.backtest.cost_bps,
            lookback_days=config.portfolio.lookback_days,
            risk_free_rate=config.portfolio.risk_free_rate,
            max_weight=config.portfolio.max_weight,
            initial_capital=config.backtest.initial_capital,
        )
        backtests = {
            "max_sharpe": tester.run("max_sharpe"),
            "equal_weight": tester.run("equal_weight"),
        }
    except FileNotFoundError:
        logger.warning("no OOS predictions found; skipping backtest section")

    markdown = render_markdown_report(
        metadata=metadata,
        forecasts={h: t.frame for h, t in tables.items()},
        portfolios=portfolios,
        backtests=backtests,
        capital=capital,
        data_range=(str(panel.dates.min().date()), str(panel.dates.max().date())),
    )
    path = save_report(markdown, config.artifacts_dir)
    console.print(f"[green]report saved:[/] {path}")


@app.command()
def pipeline(
    config_path: str | None = typer.Option(None, "--config", "-c"),
    synthetic: bool = typer.Option(
        True,
        "--synthetic/--no-synthetic",
        help="Synthetic offline mode by default; pass --no-synthetic for live yfinance data",
    ),
    quick: bool = typer.Option(False, "--quick"),
    capital: float = typer.Option(100_000.0, "--capital"),
) -> None:
    """One-shot: train -> forecast -> portfolio -> backtest -> report."""
    train(config_path=config_path, synthetic=synthetic, quick=quick)
    forecast(config_path=config_path, synthetic=synthetic)
    optimize(capital=capital, config_path=config_path, synthetic=synthetic)
    backtest(config_path=config_path, synthetic=synthetic)
    report(capital=capital, config_path=config_path, synthetic=synthetic)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"), port: int = typer.Option(8000, "--port")
) -> None:
    """Serve the REST API."""
    import uvicorn

    uvicorn.run("stockforge.api.app:app", host=host, port=port)


@app.command()
def dashboard(headless: bool = typer.Option(False, "--headless")) -> None:
    """Launch the Streamlit dashboard."""
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port", "8501"]
    if headless:
        cmd.append("--server.headless=true")
    raise typer.Exit(subprocess.call(cmd))


def main() -> None:
    """Console-script entry point (see [project.scripts] in pyproject.toml)."""
    app()


if __name__ == "__main__":
    app()
