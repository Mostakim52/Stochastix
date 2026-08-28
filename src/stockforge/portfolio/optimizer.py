"""Mean-variance family optimizers with long-only weight caps, plus HRP."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.optimize import minimize
from scipy.spatial.distance import squareform
from sklearn.covariance import LedoitWolf

from stockforge.exceptions import OptimizationError


@dataclass
class PortfolioResult:
    scheme: str
    weights: pd.Series
    exp_return: float
    exp_vol: float
    sharpe: float


def shrunk_covariance(returns: pd.DataFrame) -> pd.DataFrame:
    """Ledoit-Wolf shrinkage estimate from a (days x assets) return frame."""
    model = LedoitWolf().fit(returns.dropna())
    return pd.DataFrame(model.covariance_, index=returns.columns, columns=returns.columns)


def portfolio_stats(weights: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> tuple[float, float]:
    ret = float(weights @ mu)
    vol = float(np.sqrt(max(weights @ cov @ weights, 0.0)))
    return ret, vol


def _solve(
    objective,
    n: int,
    bounds: list[tuple[float, float]],
    max_iter: int = 1000,
    extra_constraints=(),
) -> np.ndarray:
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}, *extra_constraints]
    starts = [np.full(n, 1.0 / n)]
    rng = np.random.default_rng(0)
    starts.append(rng.dirichlet(np.ones(n)))

    last_message = "no attempt"
    for x0 in starts:
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": max_iter, "ftol": 1e-10},
        )
        if result.success or result.status == 9:  # 9 = iteration cap with usable solution
            weights = np.clip(result.x, 0.0, None)
            total = weights.sum()
            if total > 0:
                return weights / total
        last_message = str(result.message)
    raise OptimizationError(f"optimizer failed: {last_message}")


class PortfolioOptimizer:
    """Long-only optimizers over an annualized mean vector and covariance matrix."""

    def __init__(
        self,
        mu: pd.Series,
        cov: pd.DataFrame,
        risk_free_rate: float = 0.02,
        max_weight: float = 0.35,
    ) -> None:
        self.tickers = list(mu.index)
        self.mu = mu.reindex(self.tickers).fillna(0.0).to_numpy(float)
        self.cov = cov.reindex(index=self.tickers, columns=self.tickers).fillna(0.0).to_numpy(float)
        self.rf = risk_free_rate
        self.bounds = [(0.0, max_weight)] * len(self.tickers)

    def _result(self, scheme: str, weights: np.ndarray) -> PortfolioResult:
        ret, vol = portfolio_stats(weights, self.mu, self.cov)
        sharpe = (ret - self.rf) / vol if vol > 0 else float("nan")
        return PortfolioResult(scheme, pd.Series(weights, index=self.tickers), ret, vol, sharpe)

    def result_from_weights(self, scheme: str, weights: pd.Series) -> PortfolioResult:
        aligned = weights.reindex(self.tickers).fillna(0.0).to_numpy(float)
        if aligned.sum() <= 0:
            raise OptimizationError(f"{scheme} produced degenerate weights")
        return self._result(scheme, aligned / aligned.sum())

    def min_variance(self) -> PortfolioResult:
        def obj(w):
            return w @ self.cov @ w

        return self._result("min_variance", _solve(obj, len(self.mu), self.bounds))

    def max_sharpe(self) -> PortfolioResult:
        def neg_sharpe(w):
            ret, vol = portfolio_stats(w, self.mu, self.cov)
            return -(ret - self.rf) / vol if vol > 1e-9 else 1e6

        return self._result("max_sharpe", _solve(neg_sharpe, len(self.mu), self.bounds))

    def max_return(self) -> PortfolioResult:
        def neg_ret(w):
            return -(w @ self.mu)

        return self._result("max_return", _solve(neg_ret, len(self.mu), self.bounds))

    def efficient_frontier(self, n_points: int = 30) -> pd.DataFrame:
        lo_ret, _ = portfolio_stats(self.min_variance().weights.to_numpy(), self.mu, self.cov)
        hi_ret, _ = portfolio_stats(self.max_return().weights.to_numpy(), self.mu, self.cov)
        targets = np.linspace(lo_ret, hi_ret, n_points)
        rows = []
        for target in targets:
            constraint = {"type": "ineq", "fun": lambda w, t=target: w @ self.mu - t}

            def obj(w):
                return w @ self.cov @ w

            try:
                weights = _solve(obj, len(self.mu), self.bounds, extra_constraints=[constraint])
            except OptimizationError:
                continue
            ret, vol = portfolio_stats(weights, self.mu, self.cov)
            rows.append(
                {
                    "target_return": target,
                    "return": ret,
                    "volatility": vol,
                    "sharpe": (ret - self.rf) / vol if vol > 0 else np.nan,
                }
            )
        return pd.DataFrame(rows)

    def equal_weight(self) -> PortfolioResult:
        weights = np.full(len(self.tickers), 1.0 / len(self.tickers))
        return self._result("equal_weight", weights)

    def inverse_volatility(self) -> PortfolioResult:
        vols = np.sqrt(np.diag(self.cov))
        inv = np.where(vols > 0, 1.0 / vols, 0.0)
        return self._result("inverse_volatility", inv / inv.sum())

    def risk_parity(self) -> PortfolioResult:
        n = len(self.tickers)

        def rc_mismatch(w):
            port_var = w @ self.cov @ w
            marginal = self.cov @ w
            contributions = w * marginal
            target = port_var / n
            return float(np.sum((contributions - target) ** 2))

        try:
            weights = _solve(rc_mismatch, n, [(1e-4, 1.0)] * n, max_iter=2000)
        except OptimizationError:
            return self.inverse_volatility()
        return self._result("risk_parity", weights)


def hrp_weights(cov: pd.DataFrame) -> pd.Series:
    """Hierarchical Risk Parity (Lopez de Prado 2016) from a covariance matrix."""
    tickers = list(cov.columns)
    stds = np.sqrt(np.diag(cov.reindex(index=tickers, columns=tickers).to_numpy(float)))
    stds = np.where(stds > 0, stds, 1e-8)
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = cov.to_numpy(float) / np.outer(stds, stds)
    corr = np.nan_to_num(np.clip(corr, -1.0, 1.0), nan=0.0)
    np.fill_diagonal(corr, 1.0)

    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, 1.0))
    condensed = squareform(dist, checks=False)
    link = linkage(condensed, method="single")
    order = leaves_list(link)

    weights = pd.Series(1.0, index=list(order), dtype=float)
    clusters = [list(order)]
    while clusters:
        cluster = clusters.pop(0)
        if len(cluster) <= 1:
            continue
        split = len(cluster) // 2
        left, right = cluster[:split], cluster[split:]

        def cluster_variance(indices: list[int]) -> float:
            sub = cov.to_numpy(float)[np.ix_(indices, indices)]
            inv_diag = 1.0 / np.diag(sub)
            inv_diag = np.where(np.isfinite(inv_diag), inv_diag, 0.0)
            normed = inv_diag / inv_diag.sum()
            return float(normed @ sub @ normed)

        var_left, var_right = cluster_variance(left), cluster_variance(right)
        total = var_left + var_right
        alpha_left = 1.0 - var_left / total if total > 0 else 0.5
        weights[left] *= alpha_left
        weights[right] *= 1.0 - alpha_left
        clusters.extend([left, right])

    series = pd.Series(0.0, index=tickers)
    for pos, weight in weights.items():
        series.iloc[int(pos)] += float(weight)
    return series / series.sum()


SCHEMES = {
    "min_variance": lambda opt, cov: opt.min_variance(),
    "max_sharpe": lambda opt, cov: opt.max_sharpe(),
    "max_return": lambda opt, cov: opt.max_return(),
    "equal_weight": lambda opt, cov: opt.equal_weight(),
    "inverse_volatility": lambda opt, cov: opt.inverse_volatility(),
    "risk_parity": lambda opt, cov: opt.risk_parity(),
    "hrp": lambda opt, cov: opt.result_from_weights("hrp", hrp_weights(cov)),
}
