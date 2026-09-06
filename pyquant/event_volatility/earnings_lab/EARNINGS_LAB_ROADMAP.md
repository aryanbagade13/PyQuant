# Earnings Lab Roadmap

## Vision

Build a research platform that studies how options markets price earnings announcements.

Primary question:

> Can we predict when the options market is underpricing or overpricing an upcoming earnings move?

Long-term goal:

> Generate a historical dataset of earnings events, option-implied expectations, realised outcomes, and company fundamentals, then test statistical and machine-learning models.

---

# Phase 1 — Core Infrastructure

Status: In Progress

### Market Data

- [x] Alpaca provider
- [x] Spot price retrieval
- [x] Option chain retrieval
- [x] Expiry discovery
- [x] Expiry caching
- [x] MarketSnapshot integration

### Earnings Models

- [x] EarningsReport
- [x] EarningsEvent
- [x] EarningsPriceWindow
- [x] EarningsReleaseTiming
- [x] EarningsExpiryWindow
- [x] ImpliedMove

### Event Logic

- [x] ATM straddle extraction
- [x] Implied move estimation
- [x] Pre-earnings cutoff logic

---

# Phase 2 — Historical Earnings Dataset

Status: In Progress

Goal:

Generate one clean observation per earnings event.

### Build

- [x] Earnings provider interface
- [x] Alpha Vantage historical EPS retrieval
- [x] Nasdaq release timing retrieval
- [x] Historical adjusted-close retrieval
- [x] Automatic pre/post-event price windows
- [x] Historical option minute-bar retrieval
- [x] ATM straddle implied-move estimate
- [ ] Historical option surface reconstruction

### Dataset Fields

- [x] Symbol
- [x] Earnings date
- [ ] Release timing
- [ ] Market cap
- [ ] Sector

- [x] Estimated EPS
- [x] Actual EPS
- [x] EPS surprise

- [x] Estimated revenue field
- [x] Actual revenue field
- [x] Revenue surprise calculation

- [x] Pre-earnings price field
- [x] Post-earnings price field

- [x] Realised earnings move calculation
- [x] Implied earnings move field

### Dataset Infrastructure

- [x] Provider-neutral earnings interface
- [x] Validated one-row-per-event model
- [x] Duplicate-event detection
- [x] Deterministic CSV export
- [x] Offline unit tests
- [x] Weekend and market-holiday-aware window selection
- [x] End-to-end provider-to-dataset builder
- [x] Automatic pre-market/after-hours classification
- [x] Unknown-timing rejection to prevent look-ahead bias

---

# Phase 3 — Earnings Variance Extraction

Goal:

Separate ordinary volatility from earnings-event volatility.

### Build

- [ ] Short expiry selection
- [ ] Long expiry selection
- [ ] Variance decomposition
- [ ] Earnings variance estimate
- [ ] Earnings implied move estimate

### Research Questions

- [ ] How much variance is attributable to earnings?
- [ ] Does this vary by sector?
- [ ] Does this vary by market cap?

---

# Phase 4 — Statistical Research

Goal:

Understand how the market prices earnings.

### Metrics

- [ ] Realised move
- [ ] Implied move
- [ ] Move ratio

Where:

move_ratio =
realised_move / implied_move

### Research Questions

- [ ] Does the market systematically overprice earnings?
- [ ] Does the market systematically underprice earnings?
- [ ] Which companies show persistent patterns?
- [ ] Which sectors show persistent patterns?

---

# Phase 5 — Feature Engineering

Goal:

Create predictive features.

### Volatility Features

- [ ] Realised volatility
- [ ] Implied volatility
- [ ] IV-RV spread
- [ ] IV rank
- [ ] IV percentile

### Earnings Features

- [ ] Previous earnings move
- [ ] Average of last 4 earnings moves
- [ ] Earnings surprise history
- [ ] Revenue surprise history

### Market Features

- [ ] Market cap
- [ ] Sector
- [ ] Relative strength
- [ ] Trading volume

### Options Features

- [ ] ATM skew
- [ ] Put-call skew
- [ ] Term structure slope
- [ ] Straddle return history

---

# Phase 6 — Machine Learning

Goal:

Predict when the options market is wrong.

Target:

realised_move / implied_move

or

realised_move - implied_move

### Models

- [ ] Linear regression
- [ ] Logistic regression
- [ ] Random forest
- [ ] XGBoost

### Validation

- [ ] Time-series splits
- [ ] Walk-forward testing
- [ ] Out-of-sample evaluation

---

# Phase 7 — Trading Strategy Research

Goal:

Convert research into tradable signals.

### Candidate Strategies

- [ ] Long straddles when model predicts underpricing
- [ ] Short straddles when model predicts overpricing
- [ ] Volatility spread trades
- [ ] Earnings portfolio construction

### Evaluation

- [ ] Sharpe ratio
- [ ] Win rate
- [ ] Drawdown
- [ ] Capital efficiency

---

# Stretch Goals

### Advanced Modelling

- [ ] Bayesian earnings models
- [ ] Event clustering
- [ ] Regime detection

### Advanced ML

- [ ] Neural networks
- [ ] Ensemble models

### Portfolio Layer

- [ ] Multi-position risk management
- [ ] Position sizing
- [ ] Volatility targeting

### Dashboard

- [ ] Streamlit research dashboard
- [ ] Earnings scanner
- [ ] Strategy monitor
