# pyQuant

An options analytics and earnings-volatility research platform built in Python.
pyQuant combines company results, release timing, stock prices, and historical
option data to compare the move priced before earnings with the move realised
after the announcement.

## Current research result

The first verified observation reconstructs Apple’s 30 January 2025 event:

| Metric | Result |
|---|---:|
| EPS estimate / actual | $2.34 / $2.40 |
| EPS surprise | +2.56% |
| ATM straddle | $9.85 |
| Option-implied move | 4.15% |
| Realised move | 0.67% |
| Realised / implied | 16.14% |

This is one observation, not evidence of a profitable strategy. The option
estimate uses Alpaca indicative minute-bar closes rather than executable OPRA
bid/ask midpoints.

## Capabilities

- Black–Scholes pricing, implied volatility, and analytical Greeks
- Portfolio valuation and aggregated risk reporting
- Volatility-smile and volatility-surface construction
- Historical earnings retrieval through Alpha Vantage
- Before-open/after-close classification with reviewed overrides
- Holiday-aware pre/post-event price windows from Yahoo Finance
- Historical ATM-straddle reconstruction from Alpaca option bars
- Auditable, analysis-ready CSV output
- Offline automated test suite

## Project structure

```text
pyquant/
├── analysis/          volatility smiles, surfaces, and chain analysis
├── cli/               supported command-line workflows
├── data/              market-data adapters and snapshots
├── event_volatility/  earnings-event models and research pipeline
├── instruments/       financial instrument definitions
├── market/            quotes and market state
├── portfolio/         positions, portfolios, and risk reports
├── pricing/           Black–Scholes, IV, and Greeks
├── ui/                Streamlit interface
└── visualisation/     plotting functions

tests/                 offline unit and pipeline tests
examples/              local demonstrations and live API smoke checks
docs/                  architecture and research documentation
```

See [docs/architecture.md](docs/architecture.md) for the data flow and design
decisions. The research roadmap is in
[EARNINGS_LAB_ROADMAP.md](pyquant/event_volatility/earnings_lab/EARNINGS_LAB_ROADMAP.md).

## Installation

Python 3.10 or newer is required.

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and add your own credentials:

```text
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPHA_VANTAGE_API_KEY=...
```

The `.env` file and generated datasets are excluded from Git.

## Build an earnings observation

After installation, run:

```bash
pyquant-earnings AAPL \
  --event-date 2025-01-30 \
  --release-timing after_market_close
```

The reviewed timing override is required when the calendar provider labels an
announcement time as unavailable. Output is written to
`data_cache/research/aapl_earnings.csv` by default.

To retrieve earnings and stock data without reconstructing historical options:

```bash
pyquant-earnings AAPL --max-events 1 --without-implied-move
```

## Run the dashboard

```bash
streamlit run pyquant/ui/app.py
```

## Test

```bash
python -m pytest
```

Tests are offline and mock remote providers. Scripts under `examples/live_data`
make real API calls and may consume provider quota.

## Research limitations

- Alpaca historical options begin in February 2024.
- Basic-plan option bars are indicative and can differ from OPRA quotes.
- The ATM-straddle method includes ordinary expiry variance as well as earnings
  variance.
- Events with unknown release timing are rejected unless manually reviewed.
- Revenue, point-in-time sector, and market-cap enrichment remain incomplete.

The next research milestone is short/long-expiry variance decomposition to
isolate the variance attributable specifically to earnings.
