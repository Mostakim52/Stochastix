"""Black-Litterman: blend market equilibrium with model views."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _aligned(cov: pd.DataFrame, w_eq: pd.Series) -> tuple[np.ndarray, np.ndarray, list[str]]:
    tickers = list(cov.columns)
    sigma = cov.reindex(index=tickers, columns=tickers).to_numpy(float)
    weights = w_eq.reindex(tickers).fillna(0.0).to_numpy(float)
    total = weights.sum()
    if total > 0:
        weights = weights / total
    return sigma, weights, tickers


def market_implied_returns(
    cov: pd.DataFrame,
    w_eq: pd.Series,
    delta: float = 2.5,
) -> pd.Series:
    """Reverse-optimized equilibrium excess returns: pi = delta * Sigma * w_mkt."""
    sigma, weights, tickers = _aligned(cov, w_eq)
    pi = delta * sigma @ weights
    return pd.Series(pi, index=tickers)


def black_litterman(
    cov: pd.DataFrame,
    w_eq: pd.Series,
    views: pd.Series,
    tau: float = 0.05,
    delta: float = 2.5,
) -> tuple[pd.Series, pd.DataFrame]:
    """Absolute-value views on selected assets.

    ``views`` maps ticker -> expected annual (simple) return. Returns the posterior
    mean vector and covariance under the standard Black-Litterman formulas.
    """
    sigma, weights, tickers = _aligned(cov, w_eq)
    pi = delta * sigma @ weights

    view_tickers = [t for t in views.index if t in tickers]
    if not view_tickers:
        mu = pd.Series(pi, index=tickers)
        return mu, cov.copy()

    k = len(view_tickers)
    P = np.zeros((k, len(tickers)))
    Q = np.zeros(k)
    for row, ticker in enumerate(view_tickers):
        col = tickers.index(ticker)
        P[row, col] = 1.0
        Q[row] = float(views.loc[ticker])

    tau_sigma = tau * sigma
    omega = np.diag(np.diag(P @ tau_sigma @ P.T))
    omega_inv = np.linalg.inv(omega + np.eye(k) * 1e-12)

    middle = P.T @ omega_inv @ P
    inner = np.linalg.inv(np.linalg.inv(tau_sigma) + middle)
    post_mu = inner @ (np.linalg.inv(tau_sigma) @ pi + P.T @ omega_inv @ Q)
    post_sigma = sigma + inner

    mu = pd.Series(post_mu, index=tickers)
    sigma_bl = pd.DataFrame(post_sigma, index=tickers, columns=tickers)
    return mu, sigma_bl


def equilibrium_weights(
    capitalization_proxy: pd.Series | None = None, tickers: list[str] | None = None
) -> pd.Series:
    """Equal-weight proxy when market caps are unavailable."""
    if capitalization_proxy is not None and len(capitalization_proxy):
        total = capitalization_proxy.sum()
        return capitalization_proxy / total
    if tickers is None:
        raise ValueError("provide either caps or tickers")
    return pd.Series(1.0 / len(tickers), index=tickers)
