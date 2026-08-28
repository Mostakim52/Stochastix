"""Live inference: latest model x freshest features -> price forecasts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from stockforge.config import AppConfig
from stockforge.data.panel import PricePanel
from stockforge.features.pipeline import build_dataset, latest_features
from stockforge.log import get_logger
from stockforge.models.base import ReturnModel, dump_json
from stockforge.models.registry import ModelRegistry

logger = get_logger("forecast")


@dataclass
class ForecastTable:
    horizon: int
    as_of: pd.Timestamp
    frame: pd.DataFrame  # index: ticker

    def to_dict(self) -> dict:
        records = self.frame.reset_index().to_dict(orient="records")
        return {
            "horizon": self.horizon,
            "as_of": str(self.as_of.date()),
            "forecasts": records,
        }


def generate_forecasts(panel: PricePanel, config: AppConfig) -> dict[int, ForecastTable]:
    registry = ModelRegistry(Path(config.artifacts_dir) / "models")
    entry = registry.latest()
    dataset = build_dataset(panel, tuple(config.features.horizons))
    last_date, tail = latest_features(dataset)

    tables: dict[int, ForecastTable] = {}
    for horizon in config.features.horizons:
        meta = entry.metadata.get("per_horizon", {}).get(str(horizon), {})
        residual_std = float(meta.get("residual_std", np.nan))
        model = ReturnModel.load(entry.model_file(horizon))
        preds = model.predict(tail)

        last_close = panel.close.loc[last_date].reindex(preds.index)
        predicted_price = last_close * np.exp(preds)
        z = 1.96
        lower = last_close * np.exp(preds - z * residual_std)
        upper = last_close * np.exp(preds + z * residual_std)

        frame = pd.DataFrame(
            {
                "last_close": last_close.round(2),
                "predicted_log_return": preds.round(6),
                f"predicted_price_h{horizon}": predicted_price.round(2),
                "lower_95": lower.round(2),
                "upper_95": upper.round(2),
                "expected_return_pct": ((np.exp(preds) - 1.0) * 100.0).round(2),
                "direction": np.where(preds > 1e-9, "up", np.where(preds < -1e-9, "down", "flat")),
            }
        ).sort_index()

        tables[horizon] = ForecastTable(horizon=horizon, as_of=last_date, frame=frame)
        logger.info("horizon %dd: %d forecasts as of %s", horizon, len(frame), last_date.date())
    return tables


def persist_forecasts(tables: dict[int, ForecastTable], config: AppConfig) -> Path:
    out_dir = Path(config.artifacts_dir) / "forecasts"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {str(h): table.to_dict() for h, table in tables.items()}
    target = out_dir / "latest.json"
    dump_json(payload, target)
    combined = pd.concat({h: t.frame for h, t in tables.items()}, names=["horizon", "ticker"])
    combined.to_parquet(out_dir / "latest.parquet")
    return target


def load_cached_forecasts(config: AppConfig) -> dict[int, pd.DataFrame]:
    path = Path(config.artifacts_dir) / "forecasts" / "latest.parquet"
    if not path.exists():
        raise FileNotFoundError(f"no cached forecasts at {path}; run `stockforge forecast` first")
    raw = pd.read_parquet(path)
    return {int(h): sub for h, sub in raw.groupby(level="horizon")}
