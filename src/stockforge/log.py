"""Logging helpers with optional rich formatting."""

from __future__ import annotations

import logging

_CONFIGURED = False


def configure(level: str = "INFO") -> None:
    global _CONFIGURED
    root = logging.getLogger("stockforge")
    if _CONFIGURED:
        root.setLevel(level.upper())
        return
    handler: logging.Handler
    try:
        from rich.logging import RichHandler

        handler = RichHandler(rich_tracebacks=True, show_path=False, markup=False)
        formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    except ImportError:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-7s %(name)s :: %(message)s", datefmt="%H:%M:%S"
        )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level.upper())
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"stockforge.{name}")
