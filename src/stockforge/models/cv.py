"""Purged walk-forward cross-validation for financial time series."""

from __future__ import annotations

import numpy as np
import pandas as pd


class WalkForwardSplitter:
    """Expanding-window splits with an embargo gap that purges leaking targets.

    The embargo removes the last ``embargo_days`` distinct trading dates from each
    training block so that an h-day forward target computed near the boundary cannot
    peek into the test window.
    """

    def __init__(
        self, n_splits: int = 5, min_train_days: int = 504, embargo_days: int = 25
    ) -> None:
        if n_splits < 1:
            raise ValueError("n_splits must be >= 1")
        self.n_splits = n_splits
        self.min_train_days = min_train_days
        self.embargo_days = embargo_days

    def split(self, index: pd.MultiIndex) -> list[tuple[np.ndarray, np.ndarray]]:
        date_level = index.get_level_values("date")
        unique_dates = date_level.unique().sort_values()
        position_of = pd.Index(unique_dates)
        row_positions = position_of.get_indexer(date_level)

        total = len(unique_dates)
        if total <= self.min_train_days + self.embargo_days:
            raise ValueError(
                f"not enough history ({total} days) for min_train={self.min_train_days}"
            )

        available = total - self.min_train_days
        test_size = max(1, available // (self.n_splits + 1))

        folds: list[tuple[np.ndarray, np.ndarray]] = []
        for i in range(1, self.n_splits + 1):
            test_start = self.min_train_days + i * test_size
            test_end = min(test_start + test_size, total)
            if test_start >= total:
                break
            train_cutoff = test_start - self.embargo_days
            train_mask = row_positions < train_cutoff
            test_mask = (row_positions >= test_start) & (row_positions < test_end)
            folds.append((np.flatnonzero(train_mask), np.flatnonzero(test_mask)))
        return folds


def check_no_leakage(index: pd.MultiIndex, folds: list[tuple[np.ndarray, np.ndarray]]) -> bool:
    """Assert every training date is strictly before every testing date."""
    dates = index.get_level_values("date")
    for train_idx, test_idx in folds:
        if dates[train_idx].max() >= dates[test_idx].min():
            return False
    return True
