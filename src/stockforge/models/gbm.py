"""LightGBM gradient boosting wrapper."""

from __future__ import annotations

from typing import Any

import pandas as pd

from stockforge.models.base import ReturnModel


class LightGBMModel(ReturnModel):
    name = "lightgbm"

    def __init__(self, **params: Any) -> None:
        import lightgbm as lgb

        defaults: dict[str, Any] = {
            "n_estimators": 500,
            "learning_rate": 0.03,
            "num_leaves": 31,
            "min_child_samples": 40,
            "subsample": 0.9,
            "colsample_bytree": 0.8,
            "random_state": 42,
        }
        defaults.update(params)
        self.params = defaults
        self.model = lgb.LGBMRegressor(**defaults, verbosity=-1)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> LightGBMModel:
        self.model.fit(X, y)
        self.feature_names_ = list(X.columns)
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self.model.predict(X), index=X.index)

    def get_params(self) -> dict:
        return dict(self.params)

    def importance(self) -> pd.Series:
        return pd.Series(self.model.feature_importances_, index=self.feature_names_).sort_values(
            ascending=False
        )
