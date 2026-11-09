# Stochastix Research Report
_Generated 2026-11-09 14:48 UTC - run `20261109-144747_d9a669`_

> **Disclaimer:** educational software. Not investment advice. Markets are close to 
> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.

## Data

- Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, SPY
- History: 2015-01-02 to 2026-11-09
- Features: 17 engineered per (date, ticker)

## Model quality (purged walk-forward CV)

| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |
|---|---|---|---|---|---|
| 1d | drift | 0.02384 | 52.9% | -0.000 | 27810 |
| 5d | drift | 0.05162 | 56.3% | +0.000 | 27770 |
| 21d | drift | 0.10661 | 61.7% | -0.000 | 27610 |

## Forecasts

### 1-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $348.58 | $348.89 | 0.09% | $332.85 - $365.71 | up |
| AMZN | $273.11 | $273.36 | 0.09% | $260.79 - $286.53 | up |
| GOOGL | $294.59 | $294.85 | 0.09% | $281.30 - $309.06 | up |
| JPM | $337.05 | $337.36 | 0.09% | $321.85 - $353.62 | up |
| META | $642.32 | $642.90 | 0.09% | $613.34 - $673.88 | up |
| MSFT | $542.71 | $543.20 | 0.09% | $518.22 - $569.38 | up |
| NVDA | $177.02 | $177.18 | 0.09% | $169.03 - $185.72 | up |
| SPY | $746.54 | $747.21 | 0.09% | $712.85 - $783.22 | up |
| TSLA | $376.27 | $376.61 | 0.09% | $359.30 - $394.76 | up |
| XOM | $165.33 | $165.48 | 0.09% | $157.87 - $173.45 | up |

### 5-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $348.58 | $350.15 | 0.45% | $316.26 - $387.67 | up |
| AMZN | $273.11 | $274.34 | 0.45% | $247.79 - $303.74 | up |
| GOOGL | $294.59 | $295.92 | 0.45% | $267.28 - $327.62 | up |
| JPM | $337.05 | $338.57 | 0.45% | $305.80 - $374.85 | up |
| META | $642.32 | $645.21 | 0.45% | $582.77 - $714.34 | up |
| MSFT | $542.71 | $545.15 | 0.45% | $492.39 - $603.56 | up |
| NVDA | $177.02 | $177.82 | 0.45% | $160.61 - $196.87 | up |
| SPY | $746.54 | $749.90 | 0.45% | $677.32 - $830.25 | up |
| TSLA | $376.27 | $377.97 | 0.45% | $341.39 - $418.47 | up |
| XOM | $165.33 | $166.07 | 0.45% | $150.00 - $183.87 | up |

### 21-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $348.58 | $355.21 | 1.90% | $287.55 - $438.80 | up |
| AMZN | $273.11 | $278.31 | 1.90% | $225.30 - $343.80 | up |
| GOOGL | $294.59 | $300.20 | 1.90% | $243.02 - $370.83 | up |
| JPM | $337.05 | $343.47 | 1.90% | $278.05 - $424.29 | up |
| META | $642.32 | $654.55 | 1.90% | $529.87 - $808.56 | up |
| MSFT | $542.71 | $553.04 | 1.90% | $447.70 - $683.17 | up |
| NVDA | $177.02 | $180.39 | 1.90% | $146.03 - $222.83 | up |
| SPY | $746.54 | $760.75 | 1.90% | $615.84 - $939.75 | up |
| TSLA | $376.27 | $383.44 | 1.90% | $310.40 - $473.66 | up |
| XOM | $165.33 | $168.48 | 1.90% | $136.39 - $208.12 | up |

## Recommended portfolios

| Scheme | AAPL | AMZN | GOOGL | JPM | META | MSFT | NVDA | SPY | TSLA | XOM | Exp. return | Exp. vol | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **max_sharpe** | 12.7% ($12,718) | 2.5% ($2,487) | 4.8% ($4,766) | 11.7% ($11,723) | 1.7% ($1,675) | 4.2% ($4,231) | 0.4% ($388) | 35.0% ($35,000) | 0.0% ($0) | 27.0% ($27,012) | 25.39% | 11.09% | 2.11 |
| **min_variance** | 12.7% ($12,720) | 2.5% ($2,486) | 4.8% ($4,765) | 11.7% ($11,724) | 1.7% ($1,674) | 4.2% ($4,230) | 0.4% ($389) | 35.0% ($35,000) | 0.0% ($0) | 27.0% ($27,010) | 25.39% | 11.09% | 2.11 |
| **hrp** | 19.5% ($19,500) | 4.7% ($4,685) | 4.8% ($4,765) | 16.9% ($16,864) | 4.9% ($4,925) | 7.2% ($7,248) | 3.3% ($3,333) | 18.7% ($18,717) | 3.3% ($3,257) | 16.7% ($16,708) | 25.39% | 12.35% | 1.89 |
| **risk_parity** | 12.1% ($12,109) | 6.9% ($6,905) | 7.5% ($7,489) | 12.0% ($12,032) | 6.1% ($6,112) | 7.9% ($7,852) | 6.7% ($6,683) | 12.2% ($12,213) | 5.0% ($5,026) | 23.6% ($23,579) | 25.39% | 12.53% | 1.87 |

## Walk-forward backtest (out-of-sample predictions)

| Scheme | CAGR | Vol | Sharpe | MaxDD | Calmar | Turnover/trade | Excess CAGR vs equal-weight |
|---|---|---|---|---|---|---|---|
| **max_sharpe** | 17.71% | 19.87% | 0.82 | -33.79% | 0.52 | 11.41% | -16.40% |
| **equal_weight** | 32.71% | 25.80% | 1.15 | -35.62% | 0.92 | 7.00% | -1.40% |

## Methodology notes

- Targets are forward log-returns; features use only information
  available at decision time.
- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.
- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors
  with model views.
- Backtest costs: 10 bps of traded value per rebalance.