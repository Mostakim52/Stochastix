import numpy as np
import pandas as pd

from stockforge.data.panel import PricePanel
from stockforge.data.synthetic import generate_synthetic_panel
from stockforge.data.validation import clean_panel, validate_panel


def test_synthetic_panel_shapes(panel):
    assert panel.close.shape == (800, 5)
    assert list(panel.tickers) == ["AAA", "BBB", "CCC", "DDD", "EEE"]
    for field in ("open", "high", "low", "close", "volume"):
        frame = getattr(panel, field)
        assert isinstance(frame, pd.DataFrame)
        assert np.isfinite(frame.to_numpy()).all()


def test_synthetic_is_deterministic():
    a = generate_synthetic_panel(["X", "Y"], periods=300, seed=42)
    b = generate_synthetic_panel(["X", "Y"], periods=300, seed=42)
    assert np.allclose(a.close.to_numpy(), b.close.to_numpy())


def test_high_low_open_consistency(panel):
    assert (panel.high >= panel.low - 1e-9).all().all()
    body_min = np.minimum(panel.open, panel.close)
    assert (panel.high >= body_min - 1e-9).all().all()
    body_max = np.maximum(panel.open, panel.close)
    assert (panel.low <= body_max + 1e-9).all().all()


def test_log_returns(panel):
    rets = panel.log_returns()
    assert rets.shape == panel.close.shape
    assert rets.iloc[0].isna().all()
    assert np.isfinite(rets.iloc[1:].to_numpy()).all()


def test_save_load_roundtrip(panel, tmp_path):
    panel.save(tmp_path)
    loaded = PricePanel.load(tmp_path)
    assert np.allclose(loaded.close.to_numpy(), panel.close.to_numpy())
    assert list(loaded.tickers) == list(panel.tickers)


def _panel_from_close(close_values, tickers=("A", "B")):
    idx = pd.bdate_range("2024-01-01", periods=len(close_values))
    close = pd.DataFrame(close_values, index=idx, columns=list(tickers))
    high = close * 1.01
    low = close * 0.99
    open_ = close.copy()
    volume = pd.DataFrame(1e6, index=idx, columns=close.columns)
    return PricePanel(open=open_, high=high, low=low, close=close, volume=volume)


def test_validator_flags_negative_prices():
    panel = _panel_from_close([[10.0, 20.0], [12.0, -5.0]])
    issues = validate_panel(panel)
    assert any("non-positive" in issue for issue in issues)


def test_clean_panel_fills_short_gap():
    close_values = [[10.0, 50.0], [np.nan, 51.0], [np.nan, np.nan], [12.0, 52.0], [13.0, 53.0]]
    idx = pd.bdate_range("2024-01-01", periods=len(close_values))
    close = pd.DataFrame(close_values, index=idx, columns=["A", "B"])
    panel = PricePanel(
        open=close.copy(),
        high=close * 1.01,
        low=close * 0.99,
        close=close,
        volume=pd.DataFrame(100.0, index=idx, columns=["A", "B"]),
    )
    cleaned, _issues = clean_panel(panel, fill_limit=3)
    assert cleaned.close["A"].notna().all()
