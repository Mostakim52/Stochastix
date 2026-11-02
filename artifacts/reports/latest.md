# Stochastix Research Report
_Generated 2026-11-02 14:21 UTC - run `20261102-142101_18795a`_

> **Disclaimer:** educational software. Not investment advice. Markets are close to 
> efficient; any edge shown in-sample can vanish. Never trade real money on a demo model.

## Data

- Universe: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, JPM, XOM, SPY
- History: 2015-01-02 to 2026-10-30
- Features: 17 engineered per (date, ticker)

## Model quality (purged walk-forward CV)

| Horizon | Best model | RMSE | Dir. accuracy | Info coeff | Obs |
|---|---|---|---|---|---|
| 1d | drift | 0.02381 | 53.0% | -0.000 | 27750 |
| 5d | drift | 0.05162 | 56.4% | +0.000 | 27710 |
| 21d | drift | 0.10649 | 61.7% | -0.000 | 27550 |

## Forecasts

### 1-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $344.63 | $344.94 | 0.09% | $329.10 - $361.55 | up |
| AMZN | $240.35 | $240.57 | 0.09% | $229.52 - $252.15 | up |
| GOOGL | $279.84 | $280.09 | 0.09% | $267.23 - $293.58 | up |
| JPM | $337.04 | $337.34 | 0.09% | $321.85 - $353.59 | up |
| META | $614.99 | $615.54 | 0.09% | $587.27 - $645.18 | up |
| MSFT | $521.91 | $522.38 | 0.09% | $498.39 - $547.53 | up |
| NVDA | $204.64 | $204.82 | 0.09% | $195.42 - $214.69 | up |
| SPY | $755.72 | $756.40 | 0.09% | $721.66 - $792.82 | up |
| TSLA | $399.81 | $400.17 | 0.09% | $381.79 - $419.44 | up |
| XOM | $187.25 | $187.42 | 0.09% | $178.81 - $196.44 | up |

### 5-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $344.63 | $346.20 | 0.46% | $312.70 - $383.30 | up |
| AMZN | $240.35 | $241.45 | 0.46% | $218.08 - $267.32 | up |
| GOOGL | $279.84 | $281.12 | 0.46% | $253.91 - $311.24 | up |
| JPM | $337.04 | $338.58 | 0.46% | $305.81 - $374.86 | up |
| META | $614.99 | $617.80 | 0.46% | $558.01 - $683.99 | up |
| MSFT | $521.91 | $524.29 | 0.46% | $473.55 - $580.47 | up |
| NVDA | $204.64 | $205.57 | 0.46% | $185.68 - $227.60 | up |
| SPY | $755.72 | $759.17 | 0.46% | $685.70 - $840.51 | up |
| TSLA | $399.81 | $401.63 | 0.46% | $362.76 - $444.67 | up |
| XOM | $187.25 | $188.10 | 0.46% | $169.90 - $208.26 | up |

### 21-day horizon

| Ticker | Last close | Forecast price | Expected return | 95% band | Direction |
|---|---|---|---|---|---|
| AAPL | $344.63 | $351.24 | 1.92% | $284.37 - $433.85 | up |
| AMZN | $240.35 | $244.96 | 1.92% | $198.32 - $302.57 | up |
| GOOGL | $279.84 | $285.21 | 1.92% | $230.91 - $352.29 | up |
| JPM | $337.04 | $343.51 | 1.92% | $278.10 - $424.29 | up |
| META | $614.99 | $626.79 | 1.92% | $507.45 - $774.20 | up |
| MSFT | $521.91 | $531.92 | 1.92% | $430.65 - $657.02 | up |
| NVDA | $204.64 | $208.57 | 1.92% | $168.86 - $257.62 | up |
| SPY | $755.72 | $770.22 | 1.92% | $623.57 - $951.36 | up |
| TSLA | $399.81 | $407.48 | 1.92% | $329.90 - $503.31 | up |
| XOM | $187.25 | $190.84 | 1.92% | $154.51 - $235.73 | up |

## Recommended portfolios

| Scheme | AAPL | AMZN | GOOGL | JPM | META | MSFT | NVDA | SPY | TSLA | XOM | Exp. return | Exp. vol | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **max_sharpe** | 12.8% ($12,848) | 1.6% ($1,602) | 5.1% ($5,081) | 12.5% ($12,508) | 1.2% ($1,236) | 5.0% ($4,968) | 0.5% ($504) | 35.0% ($35,000) | 0.0% ($0) | 26.3% ($26,254) | 25.62% | 10.41% | 2.27 |
| **min_variance** | 12.8% ($12,847) | 1.6% ($1,600) | 5.1% ($5,081) | 12.5% ($12,509) | 1.2% ($1,236) | 5.0% ($4,968) | 0.5% ($505) | 35.0% ($35,000) | 0.0% ($0) | 26.3% ($26,254) | 25.62% | 10.41% | 2.27 |
| **hrp** | 19.4% ($19,392) | 4.2% ($4,229) | 4.5% ($4,510) | 17.8% ($17,813) | 4.6% ($4,648) | 7.6% ($7,590) | 3.3% ($3,267) | 18.9% ($18,859) | 3.1% ($3,111) | 16.6% ($16,582) | 25.62% | 11.61% | 2.03 |
| **risk_parity** | 12.4% ($12,369) | 6.5% ($6,457) | 7.4% ($7,431) | 12.6% ($12,600) | 5.7% ($5,694) | 7.9% ($7,913) | 6.6% ($6,575) | 12.4% ($12,446) | 5.0% ($4,966) | 23.5% ($23,550) | 25.62% | 11.85% | 1.99 |

## Walk-forward backtest (out-of-sample predictions)

| Scheme | CAGR | Vol | Sharpe | MaxDD | Calmar | Turnover/trade | Excess CAGR vs equal-weight |
|---|---|---|---|---|---|---|---|
| **max_sharpe** | 18.04% | 19.82% | 0.84 | -32.27% | 0.56 | 11.76% | -17.42% |
| **equal_weight** | 32.50% | 25.87% | 1.14 | -35.46% | 0.92 | 7.02% | -2.95% |

## Methodology notes

- Targets are forward log-returns; features use only information
  available at decision time.
- Walk-forward splits purge `embargo_days` between train and test to kill target leakage.
- Covariances use Ledoit-Wolf shrinkage; Black-Litterman blends equilibrium priors
  with model views.
- Backtest costs: 10 bps of traded value per rebalance.