"""End-to-end training: walk-forward evaluation, model selection, registry persistence."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from stockforge.config import AppConfig
from stockforge.data.panel import PricePanel
from stockforge.exceptions import StockForgeError
from stockforge.features.pipeline import align_xy, build_dataset
from stockforge.log import get_logger
from stockforge.models.base import ReturnModel
from stockforge.models.baseline import DriftModel, NaiveModel
from stockforge.models.cv import WalkForwardSplitter, check_no_leakage
from stockforge.models.ensemble import EnsembleModel
from stockforge.models.evaluation import regression_metrics
from stockforge.models.gbm import LightGBMModel
from stockforge.models.linear import ElasticNetModel
from stockforge.models.registry import ModelRegistry

logger = get_logger("training")

ENSEMBLE_BASES = ("naive", "drift", "elasticnet", "lightgbm")


@dataclass
class TrainOutcome:
    run_id: str
    run_dir: Path
    metadata: dict


def _candidate_factories(config: AppConfig) -> dict[str, Callable[[], ReturnModel]]:
    return {
        "naive": lambda: NaiveModel(),
        "drift": lambda: DriftModel(),
        "elasticnet": lambda: ElasticNetModel(**config.model.elasticnet.model_dump()),
        "lightgbm": lambda: LightGBMModel(**config.model.lightgbm.model_dump()),
    }


def _git_sha() -> str | None:
    return os.environ.get("GIT_SHA") or None


def train_all(panel: PricePanel, config: AppConfig) -> TrainOutcome:
    horizons = list(config.features.horizons)
    dataset = build_dataset(panel, horizons)
    splitter = WalkForwardSplitter(
        n_splits=config.cv.n_splits,
        min_train_days=config.cv.min_train_days,
        embargo_days=config.cv.embargo_days,
    )
    registry = ModelRegistry(Path(config.artifacts_dir) / "models")
    run_id, run_dir = registry.new_run()

    per_horizon: dict[str, dict] = {}
    for horizon in horizons:
        X, y = align_xy(dataset, horizon)
        folds = splitter.split(X.index)
        if not check_no_leakage(X.index, folds):
            raise StockForgeError("walk-forward folds leaked; refusing to train")

        factories = _candidate_factories(config)
        names = [n for n in config.model.candidate_names if n in factories and n != "ensemble"]
        candidates = {name: factories[name]() for name in names}

        oos_pred: dict[str, pd.Series] = {}
        oos_true: pd.Series | None = None
        fold_scores: dict[str, list[dict]] = {name: [] for name in names}

        for train_idx, test_idx in folds:
            X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
            X_te = X.iloc[test_idx]
            y_te = y.iloc[test_idx]
            oos_true = y_te if oos_true is None else pd.concat([oos_true, y_te])
            for name, model in candidates.items():
                fitted = model.fit(X_tr, y_tr)
                pred = fitted.predict(X_te)
                oos_pred[name] = pred if name not in oos_pred else pd.concat([oos_pred[name], pred])
                fold_scores[name].append(regression_metrics(y_te, pred))

        assert oos_true is not None
        pooled_rmse = {
            name: float(np.nanmean([f["rmse"] for f in scores]))
            for name, scores in fold_scores.items()
        }

        metrics_by_model = {name: pooled_rmse[name] for name in names}
        detail_by_model = {name: fold_scores[name] for name in names}

        if {"ensemble"} <= set(config.model.candidate_names) and all(
            b in oos_pred for b in ENSEMBLE_BASES
        ):
            members = [candidates[b] for b in ENSEMBLE_BASES]
            ensemble = EnsembleModel.from_validation_rmse(
                members, {b: pooled_rmse[b] for b in ENSEMBLE_BASES}
            )
            blend = pd.Series(0.0, index=oos_true.index)
            for member in members:
                weight = ensemble.weights.get(member.name, 0.0)
                blend = blend + weight * oos_pred[member.name].reindex(oos_true.index).fillna(0.0)
            ens_metrics = regression_metrics(oos_true, blend)
            metrics_by_model["ensemble"] = float(ens_metrics["rmse"])
            detail_by_model["ensemble"] = [ens_metrics]
            oos_pred["ensemble"] = blend

        best_name = min(metrics_by_model, key=lambda k: metrics_by_model[k])
        best_oos = oos_pred[best_name].reindex(oos_true.index)

        final_model: ReturnModel
        if best_name == "ensemble":
            members = [candidates[b] for b in ENSEMBLE_BASES]
            final_model = EnsembleModel.from_validation_rmse(
                members, {b: pooled_rmse[b] for b in ENSEMBLE_BASES}
            ).fit(X, y)
        else:
            final_model = candidates[best_name].fit(X, y)

        residuals = (oos_true - best_oos).dropna()
        residual_std = float(residuals.std(ddof=0)) if len(residuals) > 1 else float("nan")

        wide = best_oos.copy()
        wide.index.names = ["date", "ticker"]
        predictions_wide = wide.unstack("ticker")

        registry.save_model(final_model, horizon, run_dir)
        registry.save_predictions(predictions_wide, horizon, run_dir)

        per_horizon[str(horizon)] = {
            "best_model": best_name,
            "pooled_rmse": metrics_by_model,
            "fold_metrics": detail_by_model,
            "residual_std": residual_std,
            "n_obs": int(len(y)),
        }
        logger.info(
            "horizon %dd: best=%s rmse=%.6f dir_acc=%.3f",
            horizon,
            best_name,
            metrics_by_model[best_name],
            float(np.nanmean([f["directional_accuracy"] for f in detail_by_model[best_name]])),
        )

    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "tickers": panel.tickers,
        "date_range": [str(panel.dates.min().date()), str(panel.dates.max().date())],
        "horizons": horizons,
        "feature_names": dataset.feature_names,
        "n_features": len(dataset.feature_names),
        "per_horizon": per_horizon,
        "config": config.model_dump(),
    }
    registry.save_metadata(metadata, run_dir)
    logger.info("run %s complete", run_id)
    return TrainOutcome(run_id=run_id, run_dir=run_dir, metadata=metadata)
