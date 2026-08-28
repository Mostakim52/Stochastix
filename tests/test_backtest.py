from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from stockforge.backtest.engine import WalkForwardBacktester


@pytest.fixture
def predictions(panel):
    """Perfect-foresight stand-in: prediction at t equals the realized forward return."""
    log_ret = np.log(panel.close).diff()
    return log_ret.shift(-1).iloc[:-1]


def test_backtest_runs_and_tracks_capital(panel, predictions):
    tester = WalkForwardBacktester(
        panel,
        predictions,
        horizon=1,
        rebalance_days=21,
        cost_bps=10.0,
        lookback_days=252,
        initial_capital=100_000.0,
    )
    result = tester.run("equal_weight")
    assert len(result.equity) > 100
    assert result.equity.iloc[0] <= 100_000.0 + 1e-6
    assert (result.equity > 0).all()
    assert not result.benchmark_equity.empty


def test_backtest_metrics_present(panel, predictions):
    tester = WalkForwardBacktester(panel, predictions, horizon=1)
    result = tester.run("min_variance")
    for key in (
        "cagr",
        "volatility",
        "sharpe",
        "max_drawdown",
        "avg_turnover_per_rebalance",
        "n_rebalances",
        "benchmark_cagr",
        "excess_cagr",
    ):
        assert key in result.metrics
    assert result.metrics["n_rebalances"] > 0
    assert result.metrics["sharpe"] == result.metrics["sharpe"]  # not NaN


def test_costs_reduce_equity(panel, predictions):
    cheap = WalkForwardBacktester(panel, predictions, horizon=1, cost_bps=0.0, rebalance_days=5)
    pricey = WalkForwardBacktester(panel, predictions, horizon=1, cost_bps=50.0, rebalance_days=5)
    assert (
        pricey.run("equal_weight").equity.iloc[-1]
        <= cheap.run("equal_weight").equity.iloc[-1] + 1e-6
    )


def test_weights_history_recorded_on_rebalances(panel, predictions):
    tester = WalkForwardBacktester(panel, predictions, horizon=1, rebalance_days=42)
    result = tester.run("max_sharpe")
    assert not result.weights_history.empty
    sums = result.weights_history.sum(axis=1)
    assert np.allclose(sums, 1.0, atol=1e-6)


def test_compare_multiple_schemes(panel, predictions):
    tester = WalkForwardBacktester(panel, predictions, horizon=1)
    results = tester.compare(["equal_weight", "inverse_volatility"])
    assert set(results) == {"equal_weight", "inverse_volatility"}
    assert all(len(r.equity) > 50 for r in results.values())


def test_mismatched_predictions_raise(panel):
    empty = pd.DataFrame(columns=panel.tickers)
    with pytest.raises(ValueError):
        WalkForwardBacktester(panel, empty, horizon=1).run("equal_weight")
