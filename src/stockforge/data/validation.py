"""Data sanity checks and light cleaning for price panels."""

from __future__ import annotations

import numpy as np

from stockforge.data.panel import FIELDS, PricePanel


def validate_panel(panel: PricePanel, max_gap_days: int = 10) -> list[str]:
    """Return human-readable issues; empty list means the panel passed."""
    issues: list[str] = []
    for name in ("open", "high", "low", "close"):
        df = getattr(panel, name)
        nonfinite = int((~np.isfinite(df)).sum().sum())
        if nonfinite:
            issues.append(f"{name}: {nonfinite} non-finite values")
        negatives = int((df <= 0).sum().sum())
        if negatives:
            issues.append(f"{name}: {negatives} non-positive values")
    if (panel.volume < 0).any().any():
        issues.append("volume: negative values")
    gaps = panel.dates.to_series().diff().dt.days.dropna()
    large_gaps = gaps[gaps > max_gap_days]
    if len(large_gaps):
        issues.append(
            f"calendar: {len(large_gaps)} gap(s) exceeding {max_gap_days} days "
            f"(max {int(large_gaps.max())}d)"
        )
    high_low_violation = (panel.high + 1e-9 < panel.low).sum().sum()
    if high_low_violation:
        issues.append("ohlc: {n} rows where high < low".replace("{n}", str(high_low_violation)))
    return issues


def clean_panel(panel: PricePanel, fill_limit: int = 3) -> tuple[PricePanel, list[str]]:
    """Forward-fill small holes and drop leading warm-up rows that are still NaN."""
    cleaned = {}
    for name in ("open", "high", "low", "close"):
        cleaned[name] = getattr(panel, name).ffill(limit=fill_limit)
    cleaned["volume"] = panel.volume.fillna(0.0)
    valid_rows = cleaned["close"].notna().all(axis=1)
    first_valid = int(np.argmax(valid_rows.to_numpy())) if valid_rows.any() else 0
    for name in FIELDS:
        cleaned[name] = cleaned[name].iloc[first_valid:]
    panel = PricePanel(**cleaned)
    return panel, validate_panel(panel)


class PanelQualityReport:
    """Simple structured result bundling a panel with its validation issues."""

    def __init__(self, panel: PricePanel, issues: list[str]) -> None:
        self.panel = panel
        self.issues = issues

    @property
    def ok(self) -> bool:
        blocking = [i for i in self.issues if "non-finite" in i or "non-positive" in i]
        return not blocking
