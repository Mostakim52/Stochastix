"""Shared fixtures: deterministic synthetic market panels."""

from __future__ import annotations

import pytest

from stockforge.data.panel import PricePanel
from stockforge.data.synthetic import generate_synthetic_panel
from stockforge.features.pipeline import Dataset, build_dataset

TICKERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


@pytest.fixture(scope="session")
def panel() -> PricePanel:
    return generate_synthetic_panel(TICKERS, periods=800, seed=7)


@pytest.fixture(scope="session")
def dataset(panel: PricePanel) -> Dataset:
    return build_dataset(panel, horizons=[1, 5])
