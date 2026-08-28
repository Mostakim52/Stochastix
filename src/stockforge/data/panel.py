"""PricePanel: aligned OHLCV containers shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ("open", "high", "low", "close", "volume")


@dataclass
class PricePanel:
    """Wide OHLCV frames sharing one DatetimeIndex and one ticker axis."""

    open: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame

    def __post_init__(self) -> None:
        frames = []
        for name in FIELDS:
            df = getattr(self, name).astype(float)
            df.index = pd.to_datetime(df.index)
            df = df[~df.index.duplicated(keep="last")].sort_index()
            df.columns = [str(c).upper() for c in df.columns]
            setattr(self, name, df)
            frames.append(df)
        common_dates = frames[0].index
        common_cols = frames[0].columns
        for df in frames[1:]:
            common_dates = common_dates.intersection(df.index)
            common_cols = common_cols.intersection(df.columns)
        if len(common_dates) == 0 or len(common_cols) == 0:
            raise ValueError("PricePanel frames share no dates or tickers")
        for name in FIELDS:
            setattr(self, name, getattr(self, name).loc[common_dates, common_cols])

    @property
    def tickers(self) -> list[str]:
        return list(self.close.columns)

    @property
    def dates(self) -> pd.DatetimeIndex:
        return self.close.index

    def log_returns(self) -> pd.DataFrame:
        return np.log(self.close).diff()

    def simple_returns(self) -> pd.DataFrame:
        return self.close.pct_change()

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for name in FIELDS:
            getattr(self, name).to_parquet(directory / f"{name}.parquet")

    @classmethod
    def load(cls, directory: str | Path) -> PricePanel:
        directory = Path(directory)
        missing = [n for n in FIELDS if not (directory / f"{n}.parquet").exists()]
        if missing:
            raise FileNotFoundError(f"missing panel files in {directory}: {missing}")
        kwargs = {name: pd.read_parquet(directory / f"{name}.parquet") for name in FIELDS}
        return cls(**kwargs)
