"""Filesystem model registry: timestamped runs under ``artifacts/models``."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from stockforge.exceptions import RegistryError
from stockforge.log import get_logger
from stockforge.models.base import ReturnModel, dump_json, load_json

logger = get_logger("registry")

_RUN_PATTERN = re.compile(r"^\d{8}-\d{6}_[0-9a-f]+$")


@dataclass
class RegistryEntry:
    run_id: str
    path: Path
    metadata: dict = field(default_factory=dict)

    def model_file(self, horizon: int) -> Path:
        return self.path / f"model_h{horizon}.joblib"

    def prediction_file(self, horizon: int) -> Path:
        return self.path / f"predictions_h{horizon}.parquet"


class ModelRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_run(self) -> tuple[str, Path]:
        # UTC: run ids sort lexicographically to resolve "latest", so they must
        # come from one clock even when runs are created on different machines
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_id = f"{stamp}_{uuid.uuid4().hex[:6]}"
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        logger.info("opened registry run %s", run_id)
        return run_id, run_dir

    def save_model(self, model: ReturnModel, horizon: int, run_dir: str | Path) -> Path:
        target = Path(run_dir) / f"model_h{horizon}.joblib"
        model.save(target)
        return target

    def save_predictions(self, frame: pd.DataFrame, horizon: int, run_dir: str | Path) -> Path:
        target = Path(run_dir) / f"predictions_h{horizon}.parquet"
        frame.to_parquet(target)
        return target

    def save_metadata(self, metadata: dict, run_dir: str | Path) -> Path:
        target = Path(run_dir) / "metadata.json"
        dump_json(metadata, target)
        return target

    def list_runs(self) -> list[RegistryEntry]:
        entries: list[RegistryEntry] = []
        if not self.root.exists():
            return entries
        for child in sorted(self.root.iterdir()):
            if child.is_dir() and _RUN_PATTERN.match(child.name):
                meta_path = child / "metadata.json"
                entries.append(
                    RegistryEntry(
                        run_id=child.name,
                        path=child,
                        metadata=load_json(meta_path) if meta_path.exists() else {},
                    )
                )
        return entries

    def latest(self) -> RegistryEntry:
        runs = self.list_runs()
        complete = [r for r in runs if r.metadata]
        chosen = complete[-1] if complete else (runs[-1] if runs else None)
        if chosen is None:
            raise RegistryError(f"no trained runs found under {self.root}")
        logger.info("latest registry run: %s", chosen.run_id)
        return chosen
