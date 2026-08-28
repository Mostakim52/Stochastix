"""Data layer: ingestion, caching, synthetic generation, validation."""

from stockforge.data.ingestion import download_panel, fetch_raw, load_panel_from_cache
from stockforge.data.panel import FIELDS, PricePanel
from stockforge.data.synthetic import generate_synthetic_panel
from stockforge.data.validation import PanelQualityReport, clean_panel, validate_panel

__all__ = [
    "FIELDS",
    "PanelQualityReport",
    "PricePanel",
    "clean_panel",
    "download_panel",
    "fetch_raw",
    "generate_synthetic_panel",
    "load_panel_from_cache",
    "validate_panel",
]
