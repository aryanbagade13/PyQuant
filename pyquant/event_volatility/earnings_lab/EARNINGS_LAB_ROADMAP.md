# Earnings research roadmap

The project is deliberately staying with a transparent estimator until there
are enough reviewed historical observations to justify statistical modelling.

## Implemented

- Earnings, release-timing, stock-price, and option-data providers
- Explicit before-open and after-close event handling
- Trading-calendar-aware realised-return windows
- Historical ATM-straddle reconstruction
- Fixed-cutoff short/long-expiry selection
- Contemporaneous raw spot and option observations
- ATM implied-volatility inversion and variance decomposition
- Implied-versus-realised move comparison
- Deterministic CSV export and offline tests

## Current experiment

Apply the same documented cutoff and variance estimator to additional reviewed
events. The objective is to learn where the approximation fails before adding
features or fitting a model.

For every observation, retain:

- release timing and its source;
- contracts, strikes, expiries, prices, and timestamps;
- contemporaneous spot, rate, and dividend assumptions;
- raw and floored earnings variance; and
- signed and absolute realised return.

## Questions to answer next

- How sensitive is the estimate to the observation horizon?
- How often is raw earnings variance negative?
- How different are bar-close estimates from bid/ask midpoint estimates?
- Does the realised-to-implied ratio persist across repeated events?

## Deferred until the dataset is credible

- sector and market-cap comparisons;
- fitted historical volatility surfaces;
- predictive features and machine-learning models; and
- trading rules, portfolio construction, and performance claims.

These are research possibilities, not implemented capabilities.
