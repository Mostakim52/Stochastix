from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stockforge.portfolio.blacklitterman import (
    black_litterman,
    equilibrium_weights,
    market_implied_returns,
)
from stockforge.portfolio.optimizer import (
    PortfolioOptimizer,
    hrp_weights,
    portfolio_stats,
    shrunk_covariance,
)
from stockforge.portfolio.risk import (
    historical_cvar,
    historical_var,
    max_drawdown,
    summarize_performance,
)


@pytest.fixture
def mu_and_cov(panel):
    returns = panel.simple_returns().tail(252)
    cov = shrunk_covariance(returns)
    mu = returns.mean() * 252.0
    return mu, cov


def test_shrunk_covariance_psd_symmetric(mu_and_cov):
    _, cov = mu_and_cov
    values = cov.to_numpy()
    assert np.allclose(values, values.T)
    eigenvalues = np.linalg.eigvalsh(values)
    assert (eigenvalues > -1e-10).all()


def _assert_valid_weights(result, optimizer):
    weights = result.weights
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (weights >= -1e-9).all()
    assert (weights <= optimizer.bounds[0][1] + 1e-6).all()


def test_all_schemes_produce_valid_weights(mu_and_cov):
    mu, cov = mu_and_cov
    opt = PortfolioOptimizer(mu, cov, risk_free_rate=0.02, max_weight=0.35)
    for scheme in (
        "min_variance",
        "max_sharpe",
        "max_return",
        "equal_weight",
        "inverse_volatility",
        "risk_parity",
    ):
        result = getattr(opt, scheme)()
        _assert_valid_weights(result, opt)


def test_min_variance_beats_equal_weight_vol(mu_and_cov):
    mu, cov = mu_and_cov
    opt = PortfolioOptimizer(mu, cov)
    assert opt.min_variance().exp_vol <= opt.equal_weight().exp_vol + 1e-8


def test_risk_parity_balances_contributions(mu_and_cov):
    _, cov = mu_and_cov
    opt = PortfolioOptimizer(pd.Series(0.05, index=cov.columns), cov)
    weights = opt.risk_parity().weights.to_numpy()
    sigma = cov.to_numpy()
    contributions = weights * (sigma @ weights)
    ratio = contributions.max() / max(contributions.min(), 1e-12)
    assert ratio < 2.5


def test_hrp_valid(mu_and_cov):
    _, cov = mu_and_cov
    weights = hrp_weights(cov)
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (weights >= 0).all()


def test_frontier_sorted_and_nonempty(mu_and_cov):
    mu, cov = mu_and_cov
    opt = PortfolioOptimizer(mu, cov)
    frontier = opt.efficient_frontier(n_points=15)
    assert len(frontier) >= 5
    assert frontier["return"].is_monotonic_increasing


def test_max_sharpe_reasonable(mu_and_cov):
    mu, cov = mu_and_cov
    opt = PortfolioOptimizer(mu, cov, risk_free_rate=0.0)
    result = opt.max_sharpe()
    ret, vol = portfolio_stats(result.weights.to_numpy(), opt.mu, opt.cov)
    expected = ret / vol
    assert result.sharpe == pytest.approx(expected, rel=1e-4)


def test_market_implied_returns_shape(mu_and_cov):
    _, cov = mu_and_cov
    w_eq = equilibrium_weights(tickers=list(cov.columns))
    pi = market_implied_returns(cov, w_eq, delta=2.5)
    assert list(pi.index) == list(cov.columns)
    assert np.isfinite(pi).all()


def test_black_litterman_pulls_toward_view(mu_and_cov):
    _, cov = mu_and_cov
    tickers = list(cov.columns)
    w_eq = equilibrium_weights(tickers=tickers)
    base_mu, _ = black_litterman(cov, w_eq, pd.Series(dtype=float))
    views = pd.Series({tickers[0]: 0.30})
    view_mu, view_sigma = black_litterman(cov, w_eq, views, tau=0.1, delta=2.5)
    assert view_sigma.loc[tickers[0], tickers[0]] >= cov.loc[tickers[0], tickers[0]] - 1e-8
    lift = view_mu[tickers[0]] - base_mu[tickers[0]]
    others = (view_mu.drop(tickers[0]) - base_mu.drop(tickers[0])).mean()
    assert lift > others


def test_var_cvar_ordering():
    rng = np.random.default_rng(3)
    returns = pd.Series(rng.normal(-0.0002, 0.01, size=2000))
    var95 = historical_var(returns, 0.95)
    cvar95 = historical_cvar(returns, 0.95)
    assert var95 > 0 and cvar95 >= var95


def test_max_drawdown_known_series():
    equity = pd.Series([100, 120, 90, 110, 60])
    dd = max_drawdown(equity)
    assert dd == pytest.approx(-0.5)


def test_summarize_performance_keys(mu_and_cov):
    rng = np.random.default_rng(5)
    equity = pd.Series(100 * np.cumprod(1 + rng.normal(0.0005, 0.01, size=300)))
    stats = summarize_performance(equity)
    for key in (
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "var_95",
        "cvar_95",
    ):
        assert key in stats
