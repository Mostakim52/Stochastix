"""Risk analytics: VaR/CVaR, drawdowns, reward-to-risk ratios."""

from __future__ import annotations

import numpy as np
import pandas as pd


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Value-at-Risk as a positive loss fraction at the given confidence level."""
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    return float(-np.quantile(clean, 1.0 - confidence))


def historical_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """Conditional VaR (expected shortfall) beyond the VaR threshold."""
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    threshold = np.quantile(clean, 1.0 - confidence)
    tail = clean[clean <= threshold]
    return float(-tail.mean()) if len(tail) else float("nan")


def drawdown_series(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax()
    return equity / running_max - 1.0


def max_drawdown(equity: pd.Series) -> float:
    dd = drawdown_series(equity.dropna())
    return float(dd.min()) if len(dd) else float("nan")


def sharpe_ratio(
    returns: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0
) -> float:
    clean = returns.dropna()
    if len(clean) < 2 or clean.std(ddof=0) == 0:
        return float("nan")
    excess = clean - risk_free_rate / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / clean.std(ddof=0))


def sortino_ratio(
    returns: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0
) -> float:
    clean = returns.dropna()
    downside = clean[clean < 0]
    if len(downside) < 2 or downside.std(ddof=0) == 0:
        return float("nan")
    excess_mean = clean.mean() - risk_free_rate / periods_per_year
    return float(np.sqrt(periods_per_year) * excess_mean / downside.std(ddof=0))


def calmar_ratio(equity: pd.Series, periods_per_year: int = 252) -> float:
    clean = equity.dropna()
    if len(clean) < 2:
        return float("nan")
    years = len(clean) / periods_per_year
    cagr = (clean.iloc[-1] / clean.iloc[0]) ** (1.0 / years) - 1.0
    mdd = abs(max_drawdown(clean))
    if mdd == 0:
        return float("nan")
    return float(cagr / mdd)


def summarize_performance(
    equity: pd.Series,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
    var_confidence: float = 0.95,
) -> dict[str, float]:
    equity = equity.dropna()
    returns = equity.pct_change().dropna()
    years = len(equity) / periods_per_year
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0 if years > 0 else float("nan")
    return {
        "total_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0),
        "cagr": float(cagr),
        "volatility": float(returns.std(ddof=0) * np.sqrt(periods_per_year)),
        "sharpe": sharpe_ratio(returns, periods_per_year, risk_free_rate),
        "sortino": sortino_ratio(returns, periods_per_year, risk_free_rate),
        "max_drawdown": max_drawdown(equity),
        "calmar": calmar_ratio(equity, periods_per_year),
        "var_95": historical_var(returns, var_confidence),
        "cvar_95": historical_cvar(returns, var_confidence),
    }
