# Stochastix Design

Status: implemented. This document records the architecture decisions baked into the code.

## Goals

1. Forecast stock prices at multiple horizons with honest, leakage-free evaluation.
2. Convert forecasts into portfolios using academically-grounded optimization.
3. Prove (or disprove) strategy value with a cost-aware out-of-sample backtest.
4. Ship as production software: typed, tested, linted, containerized, CI/CD'd.

## Key decisions

| Decision | Choice | Rationale |
|---|---|---|
| Prediction target | forward log-returns per horizon (1/5/21d), not raw prices | stationary-ish, comparable across tickers, prices reconstructed via `S0 * exp(pred)` |
| Data model | wide `(date x ticker)` frames inside one `PricePanel`; stacked to long `(date, ticker)` for learning | vectorized indicator math + tidy supervision |
| Validation | expanding walk-forward with purge (`embargo_days`) between train/test | prevents h-day forward targets from leaking across the boundary |
| Model zoo | naive/drift baselines, ElasticNet, LightGBM, RMSE-weighted ensemble | cheap-to-strong ladder; baselines keep us honest about edge |
| Selection | lowest pooled walk-forward RMSE per horizon; refit on all data | standard practice; OOS predictions retained for backtesting |
| Covariance | Ledoit-Wolf shrinkage on trailing daily returns, annualized (x252) | stable inverse for optimizers; matches annualized mu units |
| Views | Black-Litterman absolute views = model expected annual returns | blends equilibrium prior with model signal, tames optimizer extremes |
| Optimizers | SLSQP with multi-start (equal-weight + Dirichlet seeds), long-only cap `max_weight`; HRP via single-linkage quasi-diagonal bisection; risk parity via contribution-matching least squares | robustness over elegance; degenerate solves fall back gracefully |
| Backtesting | replays saved OOS predictions only; trading at decision close; costs in bps per turnover | no lookahead by construction; realistic drag |
| Registry | timestamped run dirs with joblib model + predictions parquet + metadata.json | trivially inspectable, no DB dependency |
| Serving | FastAPI reads latest artifacts; retrain endpoint guarded by optional API key | read path never blocks on network; write path auditable |
| Offline mode | seeded synthetic GBM generator with AR(1) momentum + regimes | whole pipeline testable in CI without network |

## Anti-leakage contract

For any row `(t, ticker)`: features use data `<= t`; targets use `(t, t+h]`. The splitter
removes the last `embargo_days` distinct dates from each training block. `check_no_leakage`
asserts `max(train_date) < min(test_date)` before any fit. The backtester only consumes
predictions produced under this regime.

## Units contract

Expected returns fed to optimizers are annual simple returns clipped to [-95%, +300%].
Covariance inputs are annualized daily-shrunk covariance. Mixing scales silently produced
Sharpe ~19 once during development; tests now pin the annualization behavior indirectly via
sane vol magnitudes in the CLI integration test output.

## Failure philosophy

Network failures degrade to stale cache then to explicit error; optimizer failures degrade to
equal-weight inside the backtester but raise in the interactive CLI; validators report issues
instead of crashing unless prices are non-finite/non-positive.
