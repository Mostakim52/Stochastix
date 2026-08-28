"""Regularized linear regression on standardized features."""

from __future__ import annotations

import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from stockforge.models.base import ReturnModel


class ElasticNetModel(ReturnModel):
    name = "elasticnet"

    def __init__(self, alpha: float = 0.001, l1_ratio: float = 0.2) -> None:
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.pipe = make_pipeline(
            StandardScaler(),
            ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=10_000, random_state=0),
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> ElasticNetModel:
        self.pipe.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return pd.Series(self.pipe.predict(X), index=X.index)

    def get_params(self) -> dict:
        return {"alpha": self.alpha, "l1_ratio": self.l1_ratio}

    def coefficients(self, feature_names: list[str]) -> pd.Series:
        enet: ElasticNet = self.pipe.steps[-1][1]
        return pd.Series(enet.coef_, index=feature_names).sort_values(key=abs, ascending=False)
