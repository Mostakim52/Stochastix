"""One-command Stochastix runner.

Usage:
    python run.py              full experience: real market data -> models ->
                               forecasts -> portfolios -> backtest -> report
                               (falls back to offline demo data automatically
                               if the market-data download fails)
    python run.py quick        same thing on fake data, ~30 seconds, no internet
    python run.py live         force the real-market-data version
    python run.py dashboard    open the web UI at http://127.0.0.1:8000/dashboard
    python run.py serve        REST API + web UI at http://127.0.0.1:8000
    python run.py report       open the latest generated research report path

Everything lands in ./artifacts (reports, forecasts, portfolios, backtests).
Delete that folder any time for a clean slate.
"""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

CLI = [sys.executable, "-m", "stockforge.cli"]

BANNER = r"""
 ____  _             _____
/ ___|| |_ ___   ___|  ___|__  _ __ __ _  ___
\___ \| __/ _ \ / __| |_ / _ \| '__/ _` |/ _ \
 ___) | || (_) | (__|  _| (_) | | | (_| |  __/
|____/ \__\___/ \___|_|  \___/|_|  \__, |\___|
                                   |___/
AI stock forecasts + portfolio optimization
"""


def run_cli(*args: str) -> int:
    return subprocess.call(CLI + list(args))


def full_run(live_first: bool = True) -> int:
    print(BANNER)
    steps_hint = Path("artifacts") / "reports" / "latest.md"

    if live_first:
        print("[1/2] Attempting REAL market data (Yahoo Finance)...")
        code = run_cli("pipeline", "--no-synthetic")
        if code == 0:
            print("\nDone! Built from real market data.")
            _next_steps(steps_hint)
            return 0
        print(
            "\nLive download failed (offline / Yahoo unreachable). "
            "Falling back to built-in DEMO data so you still get the full tour.\n"
        )

    print("[1/1] Running on demo data...")
    code = run_cli("pipeline")
    if code == 0:
        print("\nDone! (demo data)")
        _next_steps(steps_hint)
    else:
        print("\nSomething failed above. Scroll up for the red error panel.")
    return code


def _next_steps(report_path: Path) -> None:
    exists = report_path.exists()
    print(
        "\nWhat now?"
        "\n  python run.py dashboard   <- web UI at http://127.0.0.1:8000/dashboard"
        "\n  python run.py serve       <- API + UI at http://127.0.0.1:8000"
        + (f"\n  Read the report: {report_path}" if exists else "")
        + "\n"
    )


COMMANDS = {
    "quick": lambda: full_run(live_first=False),
    "demo": lambda: full_run(live_first=False),
    "live": lambda: full_run(live_first=True),
}


def _relaunch_in_project_venv() -> int | None:
    """If started with bare Anaconda/base python, hand off to the project venv.

    The venv ships matched library versions (parquet writers vs readers etc.);
    mixing base-Anaconda pandas/pyarrow with venv-written caches breaks loudly.
    """
    if os.environ.get("STOCKFORGE_IN_VENV") == "1":
        return None
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return None
    candidates = [Path(".venv/Scripts/python.exe"), Path(".venv/bin/python")]
    venv_python = next((c.resolve() for c in candidates if c.exists()), None)
    if venv_python is None:
        return None
    if Path(sys.executable).resolve() == venv_python:
        return None
    print(f"-> Switching to the project environment ({venv_python})")
    env = {**os.environ, "STOCKFORGE_IN_VENV": "1"}
    try:
        return subprocess.call([str(venv_python), Path(__file__).resolve(), *sys.argv[1:]], env=env)
    except OSError as exc:
        print(f"Could not launch project venv ({exc}); continuing with current python.")
        return None


def main() -> int:
    handed_off = _relaunch_in_project_venv()
    if handed_off is not None:
        return handed_off

    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if arg in COMMANDS:
        return COMMANDS[arg]()
    if arg == "dashboard":
        url = "http://127.0.0.1:8000/dashboard"
        print(f"Opening Stochastix web UI at {url}")
        webbrowser.open(url)
        return 0
    if arg == "serve":
        host = "127.0.0.1"
        port = "8000"
        print(f"Serving API + Web UI at http://{host}:{port}")
        print(f"  API docs:     http://{host}:{port}/docs")
        print(f"  Web UI:       http://{host}:{port}/dashboard")
        return run_cli("serve", "--host", host, "--port", port)
    if arg in {"report", "results"}:
        path = Path("artifacts") / "reports" / "latest.md"
        print(f"Latest report: {path.resolve()}")
        print(f"Exists: {path.exists()}")
        return 0
    if arg in {"help", "-h", "--help", ""}:
        if arg == "":
            return full_run()
        print(__doc__)
        return 0

    print(f"Unknown command: {arg}\n")
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
