from __future__ import annotations

import numpy as np
import pytest

from stockforge.models.cv import WalkForwardSplitter, check_no_leakage


@pytest.fixture
def multi_index(dataset):
    return dataset.X.index


def test_fold_count(multi_index):
    splitter = WalkForwardSplitter(n_splits=4, min_train_days=504, embargo_days=25)
    folds = splitter.split(multi_index)
    assert len(folds) == 4
    for train_idx, test_idx in folds:
        assert len(train_idx) > 0 and len(test_idx) > 0


def test_train_strictly_before_test_with_embargo(multi_index):
    embargo = 30
    splitter = WalkForwardSplitter(n_splits=3, min_train_days=504, embargo_days=embargo)
    folds = splitter.split(multi_index)
    dates = multi_index.get_level_values("date")
    unique_dates = dates.unique()
    for train_idx, test_idx in folds:
        gap = unique_dates.get_loc(dates[test_idx].min()) - unique_dates.get_loc(
            dates[train_idx].max()
        )
        assert gap >= embargo


def test_check_no_leakage_true(multi_index):
    splitter = WalkForwardSplitter(n_splits=2, min_train_days=504, embargo_days=10)
    folds = splitter.split(multi_index)
    assert check_no_leakage(multi_index, folds)


def test_check_no_leakage_detects_overlap(multi_index):
    n = len(multi_index)
    bad = [(np.arange(n // 2), np.arange(n // 4, 3 * n // 4))]
    assert not check_no_leakage(multi_index, bad)


def test_insufficient_history_raises(multi_index):
    splitter = WalkForwardSplitter(n_splits=2, min_train_days=5000, embargo_days=25)
    with pytest.raises(ValueError):
        splitter.split(multi_index)


def test_expanding_windows_grow(multi_index):
    splitter = WalkForwardSplitter(n_splits=3, min_train_days=504, embargo_days=25)
    folds = splitter.split(multi_index)
    sizes = [len(t) for t, _ in folds]
    assert sizes == sorted(sizes)
