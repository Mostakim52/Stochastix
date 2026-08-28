"""Cost-aware walk-forward backtester driven by out-of-sample predictions."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from stockforge.data.panel import PricePanel
from stockforge.log import get_logger
from stockforge.portfolio.blacklitterman import black_litterman, equilibrium_weights
from stockforge.portfolio.optimizer import SCHEMES, PortfolioOptimizer, shrunk_covariance
from stockforge.portfolio.risk import summarize_performance

logger = get_logger("backtest")


@dataclass
class BacktestResult:
    scheme: str
    equity: pd.Series
    benchmark_equity: pd.Series
    weights_history: pd.DataFrame
    metrics: dict = field(default_factory=dict)


class WalkForwardBacktester:
    """Rebalances a portfolio at fixed intervals using strictly out-of-sample forecasts.

    The ``predictions`` frame maps each decision date to the model's predicted
    h-period log-return per ticker. Trading occurs at that date's close, which is
    legitimate because the prediction only depends on information up to that close.
    """

    def __init__(
        self,
        panel: PricePanel,
        predictions: pd.DataFrame,
        horizon: int,
        rebalance_days: int = 21,
        cost_bps: float = 10.0,
        lookback_days: int = 252,
        risk_free_rate: float = 0.02,
        max_weight: float = 0.35,
        initial_capital: float = 100_000.0,
    ) -> None:
        self.panel = panel
        self.predictions = predictions
        self.horizon = horizon
        self.rebalance_days = rebalance_days
        self.cost_bps = cost_bps
        self.lookback_days = lookback_days
        self.rf = risk_free_rate
        self.max_weight = max_weight
        self.capital = initial_capital

    def _annualized_mu(self, pred_row: pd.Series) -> pd.Series:
        scaled = np.exp(pred_row.astype(float).clip(-2.0, 2.0) / self.horizon * 252.0) - 1.0
        return scaled.clip(-0.95, 3.0)

    def run(
        self, scheme: str = "max_sharpe", black_litterman_views: bool = False
    ) -> BacktestResult:
        closes = self.panel.close
        returns = self.panel.simple_returns()
        preds = self.predictions.reindex(columns=closes.columns).dropna(how="all")

        sim_dates = [d for d in preds.index if d in closes.index]
        if not sim_dates:
            raise ValueError("predictions and price panel share no dates")
        first_rebalance = sim_dates[0]

        units = pd.Series(0.0, index=closes.columns)
        cash = self.capital
        weights_prev = pd.Series(0.0, index=closes.columns)

        equity: dict[pd.Timestamp, float] = {}
        weights_history: dict[pd.Timestamp, pd.Series] = {}
        turnovers: list[float] = []

        rebalance_dates = set(sim_dates[:: self.rebalance_days])

        for date in sim_dates:
            if date in rebalance_dates and date >= first_rebalance:
                hist = returns.loc[:date].tail(self.lookback_days)
                if len(hist) >= 60 and hist.notna().all(axis=1).all():
                    cov = shrunk_covariance(hist) * 252.0
                    mu_model = self._annualized_mu(preds.loc[date])
                    if black_litterman_views:
                        w_eq = equilibrium_weights(tickers=list(mu_model.index))
                        mu, _ = black_litterman(
                            cov,
                            w_eq,
                            mu_model,
                            delta=max(self.rf * 4.0, 2.5),
                        )
                        mu = mu.clip(-0.95, 3.0)
                    else:
                        mu = mu_model
                    try:
                        optimizer = PortfolioOptimizer(
                            mu, cov, risk_free_rate=self.rf, max_weight=self.max_weight
                        )
                        result = SCHEMES[scheme](optimizer, cov)
                        target = result.weights.fillna(0.0)
                    except Exception as exc:  # noqa: BLE001 - degrade to equal weight
                        logger.warning(
                            "optimizer failed on %s (%s); equal-weight fallback", date.date(), exc
                        )
                        target = pd.Series(1.0 / len(units.index), index=units.index)

                    prices = closes.loc[date]
                    port_value = float((units * prices).sum()) + cash
                    if port_value > 0:
                        desired = target * port_value
                        current = units * prices
                        trades = desired - current
                        turnover = float(trades.abs().sum() / port_value)
                        cost = port_value * turnover * self.cost_bps / 10_000.0
                        units = units + trades / prices.replace(0.0, np.nan)
                        units = units.fillna(0.0)
                        cash = cash - float(trades.sum()) - cost
                        weights_prev = target
                        turnovers.append(turnover)
                        weights_history[date] = weights_prev

            equity[date] = float((units * closes.loc[date]).sum()) + cash

        equity_series = pd.Series(equity).sort_index()

        bench_prices = closes.loc[closes.index >= sim_dates[0]]
        bench_units = pd.Series(
            self.capital / len(closes.columns) / closes.loc[sim_dates[0]], index=closes.columns
        )
        benchmark = (bench_units * bench_prices).sum(axis=1)

        metrics = summarize_performance(equity_series, risk_free_rate=self.rf)
        metrics["avg_turnover_per_rebalance"] = float(np.mean(turnovers)) if turnovers else 0.0
        metrics["n_rebalances"] = len(turnovers)
        bench_cagr = summarize_performance(benchmark, risk_free_rate=self.rf)["cagr"]
        metrics["benchmark_cagr"] = bench_cagr
        metrics["excess_cagr"] = metrics["cagr"] - bench_cagr

        weights_frame = (
            pd.DataFrame(weights_history).T.sort_index() if weights_history else pd.DataFrame()
        )
        return BacktestResult(
            scheme=scheme,
            equity=equity_series,
            benchmark_equity=benchmark,
            weights_history=weights_frame,
            metrics=metrics,
        )

    def compare(self, schemes: list[str]) -> dict[str, BacktestResult]:
        return {scheme: self.run(scheme) for scheme in schemes}
