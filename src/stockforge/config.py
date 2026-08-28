"""Typed application configuration loaded from YAML plus environment overrides."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class UniverseConfig(BaseModel):
    tickers: list[str] = Field(default_factory=lambda: ["AAPL", "MSFT", "NVDA", "SPY"])
    benchmark: str = "SPY"


class DataConfig(BaseModel):
    start: str = "2015-01-01"
    cache_dir: str = "./data/cache"
    retry_attempts: int = 3
    retry_backoff_seconds: float = 2.0


class FeaturesConfig(BaseModel):
    horizons: list[int] = Field(default_factory=lambda: [1, 5, 21])
    warmup_days: int = 210


class LightGBMParams(BaseModel):
    n_estimators: int = 500
    learning_rate: float = 0.03
    num_leaves: int = 31
    min_child_samples: int = 40
    subsample: float = 0.9
    colsample_bytree: float = 0.8
    random_state: int = 42


class ElasticNetParams(BaseModel):
    alpha: float = 0.001
    l1_ratio: float = 0.2


class ModelConfig(BaseModel):
    candidate_names: list[str] = Field(
        default_factory=lambda: ["naive", "drift", "elasticnet", "lightgbm", "ensemble"]
    )
    lightgbm: LightGBMParams = Field(default_factory=LightGBMParams)
    elasticnet: ElasticNetParams = Field(default_factory=ElasticNetParams)


class CVConfig(BaseModel):
    n_splits: int = 5
    min_train_days: int = 504
    embargo_days: int = 25


class PortfolioConfig(BaseModel):
    lookback_days: int = 252
    risk_free_rate: float = 0.02
    max_weight: float = 0.35
    delta: float = 2.5
    tau: float = 0.05
    blend_model_weight: float = 0.5


class BacktestConfig(BaseModel):
    rebalance_days: int = 21
    cost_bps: float = 10.0
    initial_capital: float = 100_000.0


class AppConfig(BaseModel):
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    cv: CVConfig = Field(default_factory=CVConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    artifacts_dir: str = "./artifacts"
    log_level: str = "INFO"


def _env_overrides() -> dict:
    overrides: dict = {}
    mapping = {
        "STOCKFORGE_ARTIFACTS_DIR": ("artifacts_dir", str),
        "STOCKFORGE_LOG_LEVEL": ("log_level", str),
        "STOCKFORGE_DATA_CACHE_DIR": ("data__cache_dir", str),
    }
    for env_name, (field, cast) in mapping.items():
        value = os.environ.get(env_name)
        if not value:
            continue
        if "__" in field:
            section, key = field.split("__", 1)
            overrides.setdefault(section, {})[key] = cast(value)
        else:
            overrides[field] = cast(value)
    return overrides


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load config from YAML (default ``configs/default.yaml``) then apply env overrides."""
    candidates = [Path(path)] if path else [Path("configs/default.yaml")]
    raw: dict = {}
    for candidate in candidates:
        if candidate.exists():
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            break
    raw.update(_env_overrides())
    return AppConfig(**raw)
