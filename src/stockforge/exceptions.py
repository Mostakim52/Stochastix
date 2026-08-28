"""Domain-specific exceptions."""


class StockForgeError(Exception):
    """Base class for all Stochastix errors."""


class DataValidationError(StockForgeError):
    """Raised when market data fails sanity checks."""


class RegistryError(StockForgeError):
    """Raised when the model registry is missing or corrupt."""


class OptimizationError(StockForgeError):
    """Raised when a portfolio optimizer cannot produce weights."""
