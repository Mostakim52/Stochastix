import numpy as np
import pandas as pd
import pytest

from stockforge.features.indicators import atr, bollinger, macd, rolling_zscore, rsi
from stockforge.features.pipeline import align_xy, latest_features


def test_rsi_bounds(panel):
    out = rsi(panel.close)
    valid = out.dropna()
    assert ((valid >= 0) & (valid <= 100)).all().all()


def test_macd_shapes(panel):
    line, signal, hist = macd(panel.close)
    for frame in (line, signal, hist):
        assert frame.shape == panel.close.shape
    assert (hist - (line - signal)).abs().max().max() < 1e-10


def test_bollinger_pctb_range(panel):
    pct_b, width = bollinger(panel.close)
    valid = pct_b.dropna()
    assert (valid.dropna() > -1.5).all().all() and (valid < 2.5).all().all()
    assert (width.dropna() >= 0).all().all()


def test_atr_positive(panel):
    out = atr(panel.high, panel.low, panel.close)
    assert (out.dropna() > 0).all().all()


def test_zscore_standardized(panel):
    z = rolling_zscore(np.log1p(panel.volume))
    recent = z.iloc[-200:]
    assert abs(recent.mean().mean()) < 0.15


EXPECTED_FEATURES = {
    "ret_1",
    "ret_5",
    "ret_10",
    "ret_21",
    "vol_10",
    "vol_21",
    "ma50_gap",
    "ma200_gap",
    "rsi_14",
    "macd_norm",
    "bb_pctb",
    "bb_width",
    "atr_pct",
    "volume_z21",
    "range_pct",
    "gap_pct",
    "rel_ret_5",
}


def test_dataset_shape_and_completeness(dataset):
    assert set(dataset.X.columns) == EXPECTED_FEATURES
    assert dataset.X.notna().all().all()
    assert np.isfinite(dataset.X.to_numpy()).all()
    assert len(dataset.X) > 400


def test_target_alignment_one_step_ahead(panel, dataset):
    y = dataset.targets[1]
    sample = y.dropna().index[:50]
    log_close = np.log(panel.close)
    for date, ticker in sample:
        expected = log_close.shift(-1).loc[date, ticker] - log_close.loc[date, ticker]
        assert y.loc[(date, ticker)] == pytest.approx(expected, abs=1e-10)


def test_targets_have_future_nan_tail(dataset):
    y5 = dataset.targets[5].dropna()
    dates = y5.index.get_level_values("date").unique()
    assert len(dates) > 0


def test_align_xy_drops_incomplete(dataset):
    X, y = align_xy(dataset, 5)
    assert len(X) == len(y)
    assert y.notna().all()


def test_latest_features_single_date(dataset):
    last_date, tail = latest_features(dataset)
    assert isinstance(last_date, pd.Timestamp)
    assert tail.notna().all().all()
    assert len(tail) == 5
