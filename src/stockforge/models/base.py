"""Model interfaces."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import joblib
import pandas as pd


class ReturnModel(ABC):
    """Predicts the h-period forward *log return* given a feature row block."""

    name: str = "base"

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> ReturnModel: ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.Series: ...

    def get_params(self) -> dict:
        return {}

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> ReturnModel:
        model = joblib.load(path)
        if not isinstance(model, ReturnModel):
            raise TypeError(f"{path} does not contain a ReturnModel")
        return model


def dump_json(payload: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
