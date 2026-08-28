"""Validation-score-weighted blending ensemble."""

from __future__ import annotations

import pandas as pd

from stockforge.models.base import ReturnModel


class EnsembleModel(ReturnModel):
    name = "ensemble"

    def __init__(
        self,
        members: list[ReturnModel],
        weights: dict[str, float] | None = None,
    ) -> None:
        self.members = members
        if weights is None:
            weights = {m.name: 1.0 / len(members) for m in members}
        total = sum(weights.values())
        self.weights = {k: v / total for k, v in weights.items()}

    @classmethod
    def from_validation_rmse(
        cls, members: list[ReturnModel], rmse_by_name: dict[str, float], floor: float = 1e-6
    ) -> EnsembleModel:
        inverse = {
            m.name: 1.0 / max(rmse_by_name.get(m.name, float("inf")), floor) ** 2 for m in members
        }
        return cls(members, inverse)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> EnsembleModel:
        for member in self.members:
            member.fit(X, y)
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        combined = pd.Series(0.0, index=X.index)
        for member in self.members:
            weight = self.weights.get(member.name, 0.0)
            if weight > 0:
                combined = combined + weight * member.predict(X)
        return combined

    def get_params(self) -> dict:
        return {"weights": self.weights, "members": [m.name for m in self.members]}
