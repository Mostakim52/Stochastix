"""Markdown research reports assembling every artifact into one document."""

from __future__ import annotations

import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _nanmean(values: list[float]) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(np.nanmean(values)) if values else float("nan")


def _fmt_pct(value: float, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n/a"
    return f"{value * 100:.{digits}f}%"


def _metrics_table(metadata: dict) -> str:
    lines = [
        "| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |",
        "|---|---|---|---|---|---|",
    ]
    for horizon, block in sorted(
        metadata.get("per_horizon", {}).items(), key=lambda kv: int(kv[0])
    ):
        best = block["best_model"]
        folds = block["fold_metrics"].get(best, [])
        rmse = block["pooled_rmse"].get(best, float("nan"))
        dir_acc = _nanmean([f.get("directional_accuracy", np.nan) for f in folds])
        ic = _nanmean([f.get("info_coefficient", np.nan) for f in folds])
        lines.append(
            f"| {horizon}d | {best} | {rmse:.5f} | {_fmt_pct(dir_acc, 1)} "
            f"| {ic:+.3f} | {block['n_obs']} |"
        )
    return "\n".join(lines)


def _forecast_table(table: pd.DataFrame, horizon: int) -> str:
    lines = [
        f"### {horizon}-day horizon",
        "",
        "| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |",
        "|---|---|---|---|---|---|",
    ]
    for ticker, row in table.iterrows():
        price_col = next(c for c in table.columns if c.startswith("predicted_price"))
        lines.append(
            f"| {ticker} | ${row['last_close']:,.2f} | ${row[price_col]:,.2f} "
            f"| {_fmt_pct(row['expected_return_pct'] / 100)} "
            f"| ${row['lower_95']:,.2f} - ${row['upper_95']:,.2f} | {row['direction']} |"
        )
    return "\n".join(lines)


def _portfolio_table(results: dict[str, Any], capital: float) -> str:
    tickers: list[str] = []
    for res in results.values():
        tickers.extend(t for t in res.weights.index if t not in tickers)
    lines = [
        "| Scheme | " + " | ".join(tickers) + " | Exp. return | Exp. vol | Sharpe |",
        "|---|" + "---|" * (len(tickers) + 3),
    ]
    for scheme, res in results.items():
        cells = [
            f"{res.weights.get(t, 0.0) * 100:.1f}% (${res.weights.get(t, 0.0) * capital:,.0f})"
            for t in tickers
        ]
        exp_ret = getattr(res, "exp_return", float("nan"))
        exp_vol = getattr(res, "exp_vol", float("nan"))
        sharpe = getattr(res, "sharpe", float("nan"))
        lines.append(
            f"| **{scheme}** | "
            + " | ".join(cells)
            + f" | {_fmt_pct(exp_ret)} | {_fmt_pct(exp_vol)} | {sharpe:.2f} |"
        )
    return "\n".join(lines)


def _backtest_table(backtests: dict[str, Any]) -> str:
    keys = ["cagr", "volatility", "sharpe", "max_drawdown", "calmar", "avg_turnover_per_rebalance"]
    header_keys = ["CAGR", "Vol", "Sharpe", "MaxDD", "Calmar", "Turnover/trade"]
    lines = [
        "| Scheme | " + " | ".join(header_keys) + " | Excess CAGR vs equal-weight |",
        "|---|" + "---|" * (len(keys) + 1),
    ]
    for scheme, result in backtests.items():
        m = result.metrics
        cells = [
            _fmt_pct(m.get("cagr")),
            _fmt_pct(m.get("volatility")),
            f"{m.get('sharpe', float('nan')):.2f}",
            _fmt_pct(m.get("max_drawdown")),
            f"{m.get('calmar', float('nan')):.2f}",
            _fmt_pct(m.get("avg_turnover_per_rebalance")),
        ]
        lines.append(
            f"| **{scheme}** | " + " | ".join(cells) + f" | {_fmt_pct(m.get('excess_cagr'))} |"
        )
    return "\n".join(lines)


def render_markdown_report(
    metadata: dict,
    forecasts: dict[int, pd.DataFrame],
    portfolios: dict[str, Any],
    backtests: dict[str, Any],
    capital: float = 100_000.0,
    data_range: tuple[str, str] | None = None,
) -> str:
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    parts = [
        "# Stochastix Research Report",
        f"_Generated {generated} - run `{metadata.get('run_id', 'unknown')}`_",
        "",
        "> **Disclaimer:** educational software. Not investment advice. Markets are close to ",
        "> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.",
        "",
        "## Data",
        "",
        f"- Universe: {', '.join(metadata.get('tickers', []))}",
        f"- History: {data_range[0]} to {data_range[1]}" if data_range else "",
        f"- Features: {metadata.get('n_features', '?')} engineered per (date, ticker)",
        "",
        "## Model quality (purged walk-forward CV)",
        "",
        _metrics_table(metadata),
        "",
        "## Forecasts",
        "",
    ]
    for horizon in sorted(forecasts):
        parts.append(_forecast_table(forecasts[horizon], horizon))
        parts.append("")
    parts += ["## Recommended portfolios", "", _portfolio_table(portfolios, capital), ""]
    if backtests:
        parts += [
            "## Walk-forward backtest (out-of-sample predictions)",
            "",
            _backtest_table(backtests),
            "",
        ]
    parts += [
        "## Methodology notes",
        "",
        "- Targets are forward log-returns; features use only information",
        "  available at decision time.",
        "- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.",
        "- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors",
        "  with model views.",
        "- Backtest costs: 10 bps of traded value per rebalance.",
    ]
    return "\n".join(p for p in parts if p is not None)


def save_report(markdown: str, artifacts_dir: str | Path) -> Path:
    out_dir = Path(artifacts_dir) / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"report_{stamp}.md"
    path.write_text(markdown, encoding="utf-8")
    latest = out_dir / "latest.md"
    latest.write_text(markdown, encoding="utf-8")
    return path
