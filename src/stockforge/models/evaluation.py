"""Forecast quality and strategy performance metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def regression_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    aligned = pd.concat([y_true.rename("t"), y_pred.rename("p")], axis=1).dropna()
    n = len(aligned)
    if n == 0:
        return {
            "rmse": float("nan"),
            "mae": float("nan"),
            "directional_accuracy": float("nan"),
            "info_coefficient": float("nan"),
            "n_obs": 0,
        }
    err = aligned["p"] - aligned["t"]
    rmse = float(np.sqrt(np.mean(err**2)))
    mae = float(np.mean(err.abs()))
    direction = float((np.sign(aligned["p"]) == np.sign(aligned["t"])).mean())
    ic = (
        float(aligned["t"].corr(aligned["p"]))
        if aligned["t"].std() > 0 and aligned["p"].std() > 0
        else float("nan")
    )
    return {
        "rmse": rmse,
        "mae": mae,
        "directional_accuracy": direction,
        "info_coefficient": ic,
        "n_obs": int(n),
    }


def annualized_sharpe(
    returns: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0
) -> float:
    clean = returns.dropna()
    if len(clean) < 2 or clean.std(ddof=0) == 0:
        return float("nan")
    excess = clean - risk_free_rate / periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / clean.std(ddof=0))


def annualized_return(equity: pd.Series, periods_per_year: int = 252) -> float:
    clean = equity.dropna()
    if len(clean) < 2 or clean.iloc[0] <= 0:
        return float("nan")
    years = len(clean) / periods_per_year
    return float((clean.iloc[-1] / clean.iloc[0]) ** (1.0 / years) - 1.0)


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    clean = returns.dropna()
    if len(clean) < 2:
        return float("nan")
    return float(clean.std(ddof=0) * np.sqrt(periods_per_year))
