"""Market data ingestion via yfinance with a local parquet cache."""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from stockforge.data.panel import FIELDS, PricePanel
from stockforge.exceptions import DataValidationError
from stockforge.log import get_logger

logger = get_logger("data")

_FIELD_ALIASES = {
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "close",
    "volume": "volume",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df.rename(columns={c: _FIELD_ALIASES.get(c, c) for c in df.columns})


def _extract_field(raw: pd.DataFrame, field: str) -> pd.DataFrame | None:
    """Pull one OHLCV field out of a yfinance frame regardless of column layout."""
    normalized = _normalize_columns(raw)
    if isinstance(normalized.columns, pd.MultiIndex):
        for level in (0, 1):
            values = normalized.columns.get_level_values(level)
            if field in values:
                out = normalized.xs(field, axis=1, level=level)
                if isinstance(out, pd.Series):
                    out = out.to_frame()
                return out
        return None
    if field in normalized.columns:
        return normalized[[field]]
    return None


def fetch_raw(
    tickers: list[str], start: str, retry_attempts: int, backoff_seconds: float
) -> pd.DataFrame:
    import yfinance as yf

    last_error: Exception | None = None
    for attempt in range(1, retry_attempts + 1):
        try:
            data = yf.download(
                tickers=tickers,
                start=start,
                progress=False,
                auto_adjust=True,
                threads=True,
            )
            if data is not None and len(data):
                return data
            last_error = DataValidationError("yfinance returned an empty frame")
        except Exception as exc:  # noqa: BLE001 - network layer can raise anything
            last_error = exc
        logger.warning("download attempt %d/%d failed: %s", attempt, retry_attempts, last_error)
        if attempt < retry_attempts:
            time.sleep(backoff_seconds * attempt)
    raise DataValidationError(
        f"could not download data after {retry_attempts} attempts: {last_error}"
    )


def _read_parquet_safe(path: Path) -> pd.DataFrame | None:
    """Read a cache file, treating corrupt/incompatible files as missing."""
    try:
        return pd.read_parquet(path)
    except Exception as exc:  # noqa: BLE001 - any reader/writer mismatch counts as corrupt
        logger.warning("cache file %s unreadable (%s); treating as missing", path.name, exc)
        return None


def _is_fresh(cache_path: Path, max_age_business_days: int = 4) -> bool:
    if not cache_path.exists():
        return False
    cached = _read_parquet_safe(cache_path)
    if cached is None or cached.empty:
        return False
    last_date = pd.Timestamp(cached.index.max())
    today = pd.Timestamp.today().normalize()
    business_days = len(pd.bdate_range(last_date, today)) - 1
    return business_days <= max_age_business_days


def _load_cached(ticker: str, cache_dir: Path) -> PricePanel | None:
    path = cache_dir / f"{ticker}.parquet"
    if not path.exists():
        return None
    df = _read_parquet_safe(path)
    if df is None:
        return None
    missing = [f for f in FIELDS if f not in df.columns]
    if missing or df.empty:
        return None
    kwargs = {name: df[[name]].rename(columns={name: ticker.upper()}) for name in FIELDS}
    try:
        return PricePanel(**kwargs)
    except ValueError:
        return None


def load_panel_from_cache(tickers: list[str], cache_dir: str | Path) -> PricePanel:
    """Rebuild a PricePanel purely from cached per-ticker parquet files."""
    cache = Path(cache_dir)
    collected: dict[str, dict[str, pd.DataFrame]] = {}
    for ticker in [t.upper() for t in tickers]:
        path = cache / f"{ticker}.parquet"
        if not path.exists():
            continue
        df = _read_parquet_safe(path)
        if df is None:
            continue
        missing = [f for f in FIELDS if f not in df.columns]
        if missing or df.empty:
            continue
        collected[ticker] = {name: df[[name]].rename(columns={name: ticker}) for name in FIELDS}
    if not collected:
        raise FileNotFoundError(f"cache at {cache} is empty; run `stockforge ingest` first")
    combined = {
        name: pd.concat([collected[t][name] for t in sorted(collected)], axis=1) for name in FIELDS
    }
    return PricePanel(**combined)


def download_panel(
    tickers: list[str],
    start: str,
    cache_dir: str | Path | None = None,
    refresh: bool = False,
    retry_attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> PricePanel:
    """Download OHLCV for all tickers, serving from the parquet cache when fresh."""
    tickers = [t.upper() for t in tickers]
    cache = Path(cache_dir) if cache_dir else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    stale: list[str] = []
    panels: dict[str, PricePanel] = {}
    for ticker in tickers:
        cache_path = cache / f"{ticker}.parquet" if cache else None
        if cache_path is not None and cache is not None and not refresh and _is_fresh(cache_path):
            panel = _load_cached(ticker, cache)
            if panel is not None:
                panels[ticker] = panel
                continue
        stale.append(ticker)

    if stale:
        logger.info("downloading %d ticker(s): %s", len(stale), ", ".join(stale))
        raw = fetch_raw(stale, start, retry_attempts, backoff_seconds)
        for ticker in stale:
            sub = raw
            if isinstance(raw.columns, pd.MultiIndex):
                level_values = raw.columns.get_level_values(-1)
                if ticker in set(level_values):
                    sub = raw.xs(ticker, axis=1, level=-1)
            fields = {}
            usable = True
            for name in ("open", "high", "low", "close", "volume"):
                extracted = _extract_field(sub, name)
                if extracted is None or extracted.dropna().empty:
                    usable = False
                    break
                fields[name] = extracted.iloc[:, 0].rename(ticker)
            if not usable:
                logger.warning("skipping %s: incomplete OHLCV data", ticker)
                continue
            frame = pd.concat(fields, axis=1)
            frame.columns = list(FIELDS)
            frame = frame.dropna(how="all")
            if cache:
                frame.to_parquet(cache / f"{ticker}.parquet")
            kwargs = {name: frame[[name]].rename(columns={name: ticker}) for name in FIELDS}
            panels[ticker] = PricePanel(**kwargs)

    if not panels:
        raise DataValidationError(f"no usable data for any of: {tickers}")

    combined = {}
    for name in FIELDS:
        combined[name] = pd.concat([panels[t].__getattribute__(name) for t in panels], axis=1)
    ordered = {
        name: combined[name].reindex(columns=[t for t in tickers if t in panels]) for name in FIELDS
    }
    return PricePanel(**ordered)
