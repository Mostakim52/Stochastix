"""Baseline models every competitor must beat."""

from __future__ import annotations

import pandas as pd

from stockforge.models.base import ReturnModel


class NaiveModel(ReturnModel):
    """Random-walk baseline: expected forward log-return is exactly zero."""

    name = "naive"

    def fit(self, X: pd.DataFrame, y: pd.Series) -> NaiveModel:
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(0.0, index=X.index)


class DriftModel(ReturnModel):
    """Constant drift estimated from the training target mean."""

    name = "drift"

    def __init__(self) -> None:
        self.drift_: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> DriftModel:
        self.drift_ = float(y.mean())
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self.drift_, index=X.index)

    def get_params(self) -> dict:
        return {"drift": self.drift_}
