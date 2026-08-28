"""Turn a PricePanel into a supervised learning dataset.

Features are computed on wide (date x ticker) frames, then stacked into a long
MultiIndex (date, ticker) table. Targets are forward log-returns over each horizon,
so ``target_h[t]`` only uses prices strictly after ``t``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from stockforge.data.panel import PricePanel
from stockforge.features import indicators as ind


@dataclass
class Dataset:
    X: pd.DataFrame
    targets: dict[int, pd.Series]
    feature_names: list[str]
    last_dates: pd.Series = field(default_factory=lambda: pd.Series(dtype="datetime64[ns]"))


def _stack(frame: pd.DataFrame) -> pd.Series:
    stacked = frame.stack()
    stacked.index.names = ["date", "ticker"]
    return stacked


def build_dataset(panel: PricePanel, horizons: list[int] | tuple[int, ...] = (1, 5, 21)) -> Dataset:
    close = panel.close
    log_close = np.log(close)
    log_ret = log_close.diff()

    features: dict[str, pd.DataFrame] = {
        "ret_1": close.pct_change(),
        "ret_5": close.pct_change(5),
        "ret_10": close.pct_change(10),
        "ret_21": close.pct_change(21),
        "vol_10": log_ret.rolling(10).std(ddof=0),
        "vol_21": log_ret.rolling(21).std(ddof=0),
        "ma50_gap": close / close.rolling(50).mean() - 1.0,
        "ma200_gap": close / close.rolling(200).mean() - 1.0,
        "rsi_14": ind.rsi(close),
        "macd_norm": ind.macd(close)[2] / close,
        "bb_pctb": ind.bollinger(close)[0],
        "bb_width": ind.bollinger(close)[1],
        "atr_pct": ind.atr(panel.high, panel.low, close) / close,
        "volume_z21": ind.rolling_zscore(np.log1p(panel.volume)),
        "range_pct": (panel.high - panel.low) / close,
        "gap_pct": panel.open / close.shift(1) - 1.0,
    }

    stacked = {name: _stack(frame.rename(columns=lambda c: c)) for name, frame in features.items()}
    X = pd.concat(stacked, axis=1)
    X.columns = list(features.keys())

    ret5 = X["ret_5"]
    cross_mean = ret5.groupby(level="date").transform("mean")
    X["rel_ret_5"] = ret5 - cross_mean

    X = X.replace([np.inf, -np.inf], np.nan)

    targets: dict[int, pd.Series] = {}
    for horizon in horizons:
        fwd = (log_close.shift(-horizon) - log_close).stack()
        fwd.index.names = ["date", "ticker"]
        targets[horizon] = fwd.rename(f"target_{horizon}")

    complete = X.dropna()
    last_per_ticker = complete.reset_index().groupby("ticker")["date"].max()
    dataset_targets = {h: s.reindex(complete.index) for h, s in targets.items()}
    return Dataset(
        X=complete,
        targets=dataset_targets,
        feature_names=list(complete.columns),
        last_dates=last_per_ticker,
    )


def latest_features(dataset: Dataset) -> tuple[pd.Timestamp, pd.DataFrame]:
    """Most recent complete feature row per ticker, for live inference."""
    X = dataset.X
    last_date = X.index.get_level_values("date").max()
    tail = X.xs(last_date, level="date", drop_level=False)
    tail.index = tail.index.droplevel("date")
    return last_date, tail.sort_index()


def align_xy(dataset: Dataset, horizon: int) -> tuple[pd.DataFrame, pd.Series]:
    """X/y pair for supervised training with incomplete futures dropped."""
    y = dataset.targets[horizon].dropna()
    common = dataset.X.index.intersection(y.index)
    return dataset.X.loc[common], y.loc[common]
