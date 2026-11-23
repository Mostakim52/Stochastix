# Stochastix Research Report
_Generated 2026-11-23 16:57 UTC - run `20261123-165722_205bfc`_

> **Disclaimer:** educational software. Not investment advice. Markets are close to 
> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.

## Data

- Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, SPY
- History: 2015-01-02 to 2026-11-23
- Features: 17 engineered per (date, ticker)

## Model quality (purged walk-forward CV)

| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |
|---|---|---|---|---|---|
| 1d | drift | 0.02393 | 52.8% | -0.000 | 27910 |
| 5d | drift | 0.05171 | 56.3% | -0.000 | 27870 |
| 21d | drift | 0.10675 | 61.6% | -0.000 | 27710 |

## Forecasts

### 1-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.89 | $348.20 | 0.09% | $332.15 - $365.02 | up |
| AMZN | $256.07 | $256.29 | 0.09% | $244.48 - $268.68 | up |
| GOOGL | $282.43 | $282.68 | 0.09% | $269.66 - $296.34 | up |
| JPM | $318.07 | $318.35 | 0.09% | $303.68 - $333.73 | up |
| META | $595.94 | $596.46 | 0.09% | $568.97 - $625.28 | up |
| MSFT | $498.46 | $498.90 | 0.09% | $475.91 - $523.00 | up |
| NVDA | $165.99 | $166.13 | 0.09% | $158.47 - $174.16 | up |
| SPY | $722.94 | $723.57 | 0.09% | $690.23 - $758.53 | up |
| TSLA | $389.82 | $390.16 | 0.09% | $372.18 - $409.01 | up |
| XOM | $158.12 | $158.26 | 0.09% | $150.97 - $165.90 | up |

### 5-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.89 | $349.42 | 0.44% | $315.56 - $386.92 | up |
| AMZN | $256.07 | $257.19 | 0.44% | $232.27 - $284.79 | up |
| GOOGL | $282.43 | $283.67 | 0.44% | $256.18 - $314.12 | up |
| JPM | $318.07 | $319.47 | 0.44% | $288.51 - $353.75 | up |
| META | $595.94 | $598.55 | 0.44% | $540.55 - $662.79 | up |
| MSFT | $498.46 | $500.65 | 0.44% | $452.13 - $554.37 | up |
| NVDA | $165.99 | $166.71 | 0.44% | $150.56 - $184.60 | up |
| SPY | $722.94 | $726.11 | 0.44% | $655.74 - $804.03 | up |
| TSLA | $389.82 | $391.53 | 0.44% | $353.59 - $433.55 | up |
| XOM | $158.12 | $158.81 | 0.44% | $143.42 - $175.86 | up |

### 21-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $347.89 | $354.39 | 1.87% | $286.84 - $437.85 | up |
| AMZN | $256.07 | $260.85 | 1.87% | $211.13 - $322.28 | up |
| GOOGL | $282.43 | $287.71 | 1.87% | $232.87 - $355.47 | up |
| JPM | $318.07 | $324.01 | 1.87% | $262.25 - $400.32 | up |
| META | $595.94 | $607.08 | 1.87% | $491.36 - $750.04 | up |
| MSFT | $498.46 | $507.77 | 1.87% | $410.99 - $627.35 | up |
| NVDA | $165.99 | $169.09 | 1.87% | $136.86 - $208.91 | up |
| SPY | $722.94 | $736.45 | 1.87% | $596.08 - $909.88 | up |
| TSLA | $389.82 | $397.10 | 1.87% | $321.41 - $490.62 | up |
| XOM | $158.12 | $161.07 | 1.87% | $130.37 - $199.01 | up |

## Recommended portfolios

| Scheme | AAPL | AMZN | GOOGL | JPM | META | MSFT | NVDA | SPY | TSLA | XOM | Exp. return | Exp. vol | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **max_sharpe** | 14.8% ($14,811) | 5.2% ($5,186) | 4.8% ($4,775) | 13.2% ($13,164) | 1.7% ($1,702) | 5.7% ($5,692) | 0.0% ($0) | 26.8% ($26,826) | 0.0% ($0) | 27.8% ($27,845) | 24.88% | 12.12% | 1.89 |
| **min_variance** | 14.8% ($14,813) | 5.2% ($5,188) | 4.8% ($4,775) | 13.2% ($13,162) | 1.7% ($1,701) | 5.7% ($5,692) | 0.0% ($0) | 26.8% ($26,826) | 0.0% ($0) | 27.8% ($27,844) | 24.88% | 12.12% | 1.89 |
| **hrp** | 20.5% ($20,476) | 5.4% ($5,358) | 5.4% ($5,394) | 17.1% ($17,063) | 5.3% ($5,296) | 7.8% ($7,844) | 2.2% ($2,211) | 15.1% ($15,149) | 3.5% ($3,452) | 17.8% ($17,757) | 24.88% | 13.29% | 1.72 |
| **risk_parity** | 12.6% ($12,628) | 7.6% ($7,601) | 7.7% ($7,744) | 12.0% ($12,020) | 6.4% ($6,353) | 8.5% ($8,531) | 5.0% ($5,045) | 11.5% ($11,505) | 5.2% ($5,243) | 23.3% ($23,330) | 24.88% | 13.69% | 1.67 |

## Walk-forward backtest (out-of-sample predictions)

| Scheme | CAGR | Vol | Sharpe | MaxDD | Calmar | Turnover/trade | Excess CAGR vs equal-weight |
|---|---|---|---|---|---|---|---|
| **max_sharpe** | 18.04% | 19.83% | 0.84 | -33.81% | 0.53 | 11.32% | -15.28% |
| **equal_weight** | 32.45% | 25.75% | 1.14 | -35.55% | 0.91 | 6.98% | -0.87% |

## Methodology notes

- Targets are forward log-returns; features use only information
  available at decision time.
- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.
- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors
  with model views.
- Backtest costs: 10 bps of traded value per rebalance.