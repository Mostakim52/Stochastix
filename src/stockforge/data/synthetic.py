"""Offline synthetic market data generator.

Produces correlated geometric-Brownian-motion panels with an AR(1) momentum factor,
regime shifts, and realistic intraday ranges so the full ML pipeline can be exercised
without network access (tests, CI, demos).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from stockforge.data.panel import PricePanel


def generate_synthetic_panel(
    tickers: list[str],
    periods: int = 900,
    seed: int = 42,
    end: str | None = None,
) -> PricePanel:
    rng = np.random.default_rng(seed)
    n = len(tickers)
    dates = pd.bdate_range(end=end or pd.Timestamp.today().normalize(), periods=periods)

    beta = rng.uniform(0.6, 1.5, size=n)
    idio_vol = rng.uniform(0.12, 0.35, size=n) / np.sqrt(252.0)
    factor_vol = 0.10 / np.sqrt(252.0)
    phi = 0.18

    regime_len = max(periods // 4, 60)
    n_regimes = int(np.ceil(periods / regime_len))
    drifts = rng.uniform(-0.0006, 0.0015, size=n_regimes)
    vols = rng.uniform(0.7, 1.6, size=n_regimes)
    regime_idx = np.repeat(np.arange(n_regimes), regime_len)[:periods]

    factor = np.zeros(periods)
    shocks = rng.normal(0.0, 1.0, size=periods)
    for t in range(1, periods):
        factor[t] = phi * factor[t - 1] + factor_vol * shocks[t]

    daily_drift = drifts[regime_idx][:, None]
    daily_vol = vols[regime_idx][:, None]
    market = factor[:, None]
    idio = rng.normal(0.0, 1.0, size=(periods, n))
    returns = daily_drift + beta * market + idio_vol * idio * daily_vol

    s0 = rng.uniform(40.0, 400.0, size=n)
    log_paths = np.cumsum(returns, axis=0)
    close = s0 * np.exp(log_paths)
    close = pd.DataFrame(close, index=dates, columns=tickers)

    open_noise = pd.DataFrame(
        rng.normal(0.0, 0.003, size=close.shape), index=dates, columns=tickers
    )
    open_ = close.shift(1) * (1.0 + open_noise)
    open_.iloc[0] = s0

    hi_noise = pd.DataFrame(
        np.abs(rng.normal(0.0, 0.006, size=close.shape)), index=dates, columns=tickers
    )
    lo_noise = pd.DataFrame(
        np.abs(rng.normal(0.0, 0.006, size=close.shape)), index=dates, columns=tickers
    )
    high = np.maximum(open_, close) * (1.0 + hi_noise)
    low = np.minimum(open_, close) * (1.0 - lo_noise)

    volume = pd.DataFrame(
        1e6 * np.exp(rng.normal(11.5, 0.6, size=close.shape)) * (1.0 + 25.0 * np.abs(returns)),
        index=dates,
        columns=tickers,
    ).round()

    return PricePanel(open=open_, high=high, low=low, close=close, volume=volume)
