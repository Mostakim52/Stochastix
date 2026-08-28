"""API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    latest_run: str | None = None


class TickerResponse(BaseModel):
    tickers: list[str]
    benchmark: str


class ForecastRecord(BaseModel):
    ticker: str
    last_close: float | None = None
    predicted_price: float | None = None
    expected_return_pct: float | None = None
    direction: str | None = None


class ForecastResponse(BaseModel):
    horizon_days: int
    as_of: str
    model_run: str | None = None
    forecasts: list[ForecastRecord]


class PortfolioRequest(BaseModel):
    capital: float = Field(default=100_000.0, gt=0)
    schemes: list[str] = Field(
        default_factory=lambda: ["max_sharpe", "min_variance", "risk_parity", "hrp"]
    )
    black_litterman: bool = False


class PortfolioAllocation(BaseModel):
    scheme: str
    weights: dict[str, float]
    dollar_allocation: dict[str, float]
    exp_return: float | None = None
    exp_vol: float | None = None
    sharpe: float | None = None


class PortfolioResponse(BaseModel):
    as_of: str
    capital: float
    allocations: list[PortfolioAllocation]


class RetrainRequest(BaseModel):
    synthetic: bool = False


class TaskAccepted(BaseModel):
    status: str
    detail: str
