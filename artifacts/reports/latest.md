# Stochastix Research Report
_Generated 2026-10-26 11:58 UTC - run `20261026-115806_4b806c`_

> **Disclaimer:** educational software. Not investment advice. Markets are close to 
> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.

## Data

- Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, SPY
- History: 2015-01-02 to 2026-10-23
- Features: 17 engineered per (date, ticker)

## Model quality (purged walk-forward CV)

| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |
|---|---|---|---|---|---|
| 1d | drift | 0.02382 | 53.0% | +0.000 | 27700 |
| 5d | drift | 0.05162 | 56.4% | -0.000 | 27660 |
| 21d | drift | 0.10648 | 61.7% | +0.000 | 27500 |

## Forecasts

### 1-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.73 | $348.05 | 0.09% | $332.05 - $364.81 | up |
| AMZN | $248.00 | $248.23 | 0.09% | $236.82 - $260.18 | up |
| GOOGL | $320.21 | $320.50 | 0.09% | $305.77 - $335.94 | up |
| JPM | $331.58 | $331.88 | 0.09% | $316.63 - $347.87 | up |
| META | $642.62 | $643.20 | 0.09% | $613.65 - $674.18 | up |
| MSFT | $524.51 | $524.99 | 0.09% | $500.86 - $550.27 | up |
| NVDA | $210.96 | $211.15 | 0.09% | $201.45 - $221.32 | up |
| SPY | $759.97 | $760.66 | 0.09% | $725.71 - $797.29 | up |
| TSLA | $372.22 | $372.56 | 0.09% | $355.44 - $390.50 | up |
| XOM | $183.21 | $183.38 | 0.09% | $174.95 - $192.21 | up |

### 5-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.73 | $349.33 | 0.46% | $315.52 - $386.76 | up |
| AMZN | $248.00 | $249.14 | 0.46% | $225.03 - $275.83 | up |
| GOOGL | $320.21 | $321.68 | 0.46% | $290.55 - $356.15 | up |
| JPM | $331.58 | $333.10 | 0.46% | $300.87 - $368.79 | up |
| META | $642.62 | $645.57 | 0.46% | $583.09 - $714.74 | up |
| MSFT | $524.51 | $526.92 | 0.46% | $475.92 - $583.38 | up |
| NVDA | $210.96 | $211.93 | 0.46% | $191.42 - $234.64 | up |
| SPY | $759.97 | $763.46 | 0.46% | $689.57 - $845.26 | up |
| TSLA | $372.22 | $373.93 | 0.46% | $337.74 - $414.00 | up |
| XOM | $183.21 | $184.05 | 0.46% | $166.24 - $203.77 | up |

### 21-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.73 | $354.42 | 1.92% | $286.91 - $437.81 | up |
| AMZN | $248.00 | $252.77 | 1.92% | $204.62 - $312.24 | up |
| GOOGL | $320.21 | $326.37 | 1.92% | $264.20 - $403.16 | up |
| JPM | $331.58 | $337.96 | 1.92% | $273.58 - $417.47 | up |
| META | $642.62 | $654.98 | 1.92% | $530.22 - $809.09 | up |
| MSFT | $524.51 | $534.60 | 1.92% | $432.77 - $660.38 | up |
| NVDA | $210.96 | $215.02 | 1.92% | $174.06 - $265.61 | up |
| SPY | $759.97 | $774.58 | 1.92% | $627.04 - $956.84 | up |
| TSLA | $372.22 | $379.38 | 1.92% | $307.12 - $468.64 | up |
| XOM | $183.21 | $186.73 | 1.92% | $151.16 - $230.67 | up |

## Recommended portfolios

| Scheme | AAPL | AMZN | GOOGL | JPM | META | MSFT | NVDA | SPY | TSLA | XOM | Exp. return | Exp. vol | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **max_sharpe** | 12.5% ($12,467) | 1.7% ($1,670) | 5.1% ($5,132) | 12.7% ($12,661) | 1.2% ($1,160) | 5.1% ($5,116) | 0.4% ($389) | 35.0% ($35,000) | 0.0% ($0) | 26.4% ($26,406) | 25.68% | 10.43% | 2.27 |
| **min_variance** | 12.5% ($12,467) | 1.7% ($1,669) | 5.1% ($5,133) | 12.7% ($12,661) | 1.2% ($1,161) | 5.1% ($5,116) | 0.4% ($388) | 35.0% ($35,000) | 0.0% ($0) | 26.4% ($26,407) | 25.68% | 10.43% | 2.27 |
| **hrp** | 19.2% ($19,181) | 4.2% ($4,202) | 5.0% ($5,000) | 17.8% ($17,779) | 4.6% ($4,610) | 7.5% ($7,490) | 3.2% ($3,164) | 19.0% ($18,968) | 3.0% ($3,047) | 16.6% ($16,558) | 25.68% | 11.67% | 2.03 |
| **risk_parity** | 12.2% ($12,171) | 6.6% ($6,589) | 7.4% ($7,449) | 12.6% ($12,637) | 5.6% ($5,629) | 7.9% ($7,948) | 6.5% ($6,507) | 12.6% ($12,596) | 5.0% ($4,969) | 23.5% ($23,506) | 25.68% | 11.93% | 1.98 |

## Walk-forward backtest (out-of-sample predictions)

| Scheme | CAGR | Vol | Sharpe | MaxDD | Calmar | Turnover/trade | Excess CAGR vs equal-weight |
|---|---|---|---|---|---|---|---|
| **max_sharpe** | 18.17% | 19.84% | 0.84 | -32.31% | 0.56 | 11.68% | -17.78% |
| **equal_weight** | 32.79% | 25.90% | 1.15 | -35.37% | 0.93 | 6.99% | -3.15% |

## Methodology notes

- Targets are forward log-returns; features use only information
  available at decision time.
- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.
- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors
  with model views.
- Backtest costs: 10 bps of traded value per rebalance.