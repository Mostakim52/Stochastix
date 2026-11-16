# Stochastix Research Report
_Generated 2026-11-16 14:23 UTC - run `20261116-142333_b91e2e`_

> **Disclaimer:** educational software. Not investment advice. Markets are close to 
> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.

## Data

- Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, SPY
- History: 2015-01-02 to 2026-11-13
- Features: 17 engineered per (date, ticker)

## Model quality (purged walk-forward CV)

| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |
|---|---|---|---|---|---|
| 1d | drift | 0.02389 | 52.9% | +0.000 | 27850 |
| 5d | drift | 0.05171 | 56.3% | -0.000 | 27810 |
| 21d | drift | 0.10661 | 61.7% | -0.000 | 27650 |

## Forecasts

### 1-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $356.27 | $356.59 | 0.09% | $340.17 - $373.80 | up |
| AMZN | $266.66 | $266.90 | 0.09% | $254.61 - $279.78 | up |
| GOOGL | $295.77 | $296.03 | 0.09% | $282.41 - $310.32 | up |
| JPM | $346.19 | $346.50 | 0.09% | $330.55 - $363.22 | up |
| META | $641.69 | $642.26 | 0.09% | $612.70 - $673.25 | up |
| MSFT | $523.88 | $524.35 | 0.09% | $500.21 - $549.65 | up |
| NVDA | $162.85 | $163.00 | 0.09% | $155.49 - $170.86 | up |
| SPY | $754.37 | $755.05 | 0.09% | $720.29 - $791.48 | up |
| TSLA | $390.22 | $390.57 | 0.09% | $372.59 - $409.42 | up |
| XOM | $170.59 | $170.74 | 0.09% | $162.88 - $178.98 | up |

### 5-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $356.27 | $357.87 | 0.45% | $323.19 - $396.27 | up |
| AMZN | $266.66 | $267.86 | 0.45% | $241.90 - $296.60 | up |
| GOOGL | $295.77 | $297.10 | 0.45% | $268.31 - $328.98 | up |
| JPM | $346.19 | $347.75 | 0.45% | $314.05 - $385.06 | up |
| META | $641.69 | $644.58 | 0.45% | $582.11 - $713.74 | up |
| MSFT | $523.88 | $526.24 | 0.45% | $475.24 - $582.70 | up |
| NVDA | $162.85 | $163.58 | 0.45% | $147.73 - $181.13 | up |
| SPY | $754.37 | $757.76 | 0.45% | $684.33 - $839.07 | up |
| TSLA | $390.22 | $391.97 | 0.45% | $353.99 - $434.03 | up |
| XOM | $170.59 | $171.36 | 0.45% | $154.75 - $189.74 | up |

### 21-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $356.27 | $363.01 | 1.89% | $293.87 - $448.43 | up |
| AMZN | $266.66 | $271.71 | 1.89% | $219.95 - $335.64 | up |
| GOOGL | $295.77 | $301.37 | 1.89% | $243.96 - $372.28 | up |
| JPM | $346.19 | $352.74 | 1.89% | $285.55 - $435.74 | up |
| META | $641.69 | $653.83 | 1.89% | $529.29 - $807.68 | up |
| MSFT | $523.88 | $533.79 | 1.89% | $432.12 - $659.39 | up |
| NVDA | $162.85 | $165.93 | 1.89% | $134.33 - $204.97 | up |
| SPY | $754.37 | $768.65 | 1.89% | $622.24 - $949.50 | up |
| TSLA | $390.22 | $397.60 | 1.89% | $321.87 - $491.16 | up |
| XOM | $170.59 | $173.82 | 1.89% | $140.71 - $214.72 | up |

## Recommended portfolios

| Scheme | AAPL | AMZN | GOOGL | JPM | META | MSFT | NVDA | SPY | TSLA | XOM | Exp. return | Exp. vol | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **max_sharpe** | 12.4% ($12,388) | 3.1% ($3,139) | 4.8% ($4,820) | 11.0% ($11,038) | 1.8% ($1,779) | 4.2% ($4,151) | 0.4% ($413) | 35.0% ($35,000) | 0.0% ($0) | 27.3% ($27,272) | 25.23% | 11.09% | 2.10 |
| **min_variance** | 12.4% ($12,389) | 3.1% ($3,140) | 4.8% ($4,819) | 11.0% ($11,036) | 1.8% ($1,779) | 4.1% ($4,150) | 0.4% ($412) | 35.0% ($35,000) | 0.0% ($0) | 27.3% ($27,274) | 25.23% | 11.09% | 2.10 |
| **hrp** | 19.5% ($19,488) | 4.8% ($4,835) | 4.9% ($4,936) | 16.7% ($16,686) | 4.9% ($4,898) | 7.1% ($7,147) | 4.4% ($4,378) | 18.4% ($18,386) | 2.4% ($2,415) | 16.8% ($16,831) | 25.23% | 12.29% | 1.89 |
| **risk_parity** | 11.9% ($11,944) | 7.0% ($7,037) | 7.6% ($7,646) | 11.8% ($11,819) | 6.2% ($6,167) | 7.9% ($7,865) | 6.7% ($6,688) | 12.1% ($12,113) | 5.0% ($5,028) | 23.7% ($23,692) | 25.23% | 12.46% | 1.86 |

## Walk-forward backtest (out-of-sample predictions)

| Scheme | CAGR | Vol | Sharpe | MaxDD | Calmar | Turnover/trade | Excess CAGR vs equal-weight |
|---|---|---|---|---|---|---|---|
| **max_sharpe** | 17.71% | 19.87% | 0.82 | -33.79% | 0.52 | 11.41% | -15.90% |
| **equal_weight** | 32.71% | 25.80% | 1.15 | -35.62% | 0.92 | 7.00% | -0.91% |

## Methodology notes

- Targets are forward log-returns; features use only information
  available at decision time.
- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.
- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors
  with model views.
- Backtest costs: 10 bps of traded value per rebalance.