from __future__ import annotations

from typer.testing import CliRunner

from stockforge import __version__
from stockforge.cli import app
from stockforge.config import AppConfig, load_config

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_load_config_defaults():
    config = load_config("configs/default.yaml")
    assert "AAPL" in config.universe.tickers
    assert config.features.horizons == [1, 5, 21]


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("STOCKFORGE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("STOCKFORGE_ARTIFACTS_DIR", "/tmp/elsewhere")
    config = load_config("nonexistent-path.yaml")
    assert config.log_level == "DEBUG"
    assert config.artifacts_dir == "/tmp/elsewhere"


def test_appconfig_serializes_roundtrip():
    config = AppConfig()
    payload = config.model_dump()
    restored = AppConfig(**payload)
    assert restored == config


def test_full_pipeline_synthetic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["pipeline", "--synthetic", "--quick"],
        env={
            "STOCKFORGE_ARTIFACTS_DIR": str(tmp_path / "artifacts"),
            "STOCKFORGE_DATA_CACHE_DIR": str(tmp_path / "cache"),
        },
    )
    assert result.exit_code == 0, result.output

    artifacts = tmp_path / "artifacts"
    assert any((artifacts / "models").iterdir())
    assert (artifacts / "forecasts" / "latest.parquet").exists()
    assert (artifacts / "portfolios" / "latest.json").exists()
    assert (artifacts / "backtest" / "metrics.json").exists()
    reports = list((artifacts / "reports").glob("report_*.md"))
    assert reports
    report_text = reports[0].read_text(encoding="utf-8")
    assert "# Stochastix Research Report" in report_text
    assert "Disclaimer" in report_text


def test_ingest_synthetic_command(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["ingest", "--synthetic"])
    assert result.exit_code == 0, result.output
    assert "Ingested market data" in result.output
