"""Classic technical indicators implemented on wide (date x ticker) frames."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    return out.fillna(50.0).where(avg_loss.notna(), 50.0)


def macd(
    close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    signal_line = line.ewm(span=signal, adjust=False).mean()
    hist = line - signal_line
    return line, signal_line, hist


def bollinger(
    close: pd.DataFrame, n: int = 20, k: float = 2.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    mid = close.rolling(n).mean()
    std = close.rolling(n).std(ddof=0)
    upper = mid + k * std
    lower = mid - k * std
    pct_b = (close - lower) / (upper - lower).replace(0.0, np.nan)
    width = (upper - lower) / mid
    return pct_b, width


def true_range(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    prev_close = close.shift(1)
    a = high - low
    b = (high - prev_close).abs()
    c = (low - prev_close).abs()
    return pd.concat([a, b, c], axis=0).groupby(level=0).max()


def atr(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    tr = true_range(high, low, close)
    tr = tr.reindex_like(close)
    return tr.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def rolling_zscore(frame: pd.DataFrame, n: int = 21) -> pd.DataFrame:
    mean = frame.rolling(n).mean()
    std = frame.rolling(n).std(ddof=0)
    return (frame - mean) / std.replace(0.0, np.nan)
