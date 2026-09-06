# Architecture

## Earnings research flow

```text
Alpha Vantage                    Nasdaq / reviewed override
quarterly EPS reports            release timing
          │                              │
          └──────────────┬───────────────┘
                         ▼
                 earnings event date
                         │
          ┌──────────────┴───────────────┐
          ▼                              ▼
Yahoo Finance                       Alpaca
adjusted and raw closes             expired option contracts + minute bars
          │                              │
          ▼                              ▼
realised return                  pre-cutoff ATM straddle
          │                              │
          └──────────────┬───────────────┘
                         ▼
             HistoricalEarningsRecord
                         │
                         ▼
               auditable research CSV
```

## Design boundaries

Provider protocols isolate external services from the research models. Tests
use small in-memory providers, allowing calculations and date-selection rules
to run without credentials or network access.

`HistoricalEarningsRecord` is the stable output boundary. It stores derived
metrics alongside the contract symbols, timestamps, strike, expiry, prices,
and source needed to audit an implied-move observation.

The command-line layer coordinates providers but does not contain pricing
maths. The Streamlit UI is another consumer of the same underlying packages.

## Look-ahead controls

- Before-open announcements use the preceding trading session.
- After-close announcements use the release-day close.
- Unknown and during-market-hours timings are rejected.
- Option bars after 3:55 p.m. New York time are excluded.
- Option bars more than 60 minutes old at the cutoff are rejected.
- Raw spot is used with option strikes; adjusted closes are used for returns.

## Data quality

The current implied move is:

```text
(ATM call bar close + ATM put bar close) / raw underlying close
```

It is a transparent approximation. A stronger estimate will compare total
variance in expiries immediately before and after the announcement, reducing
the ordinary non-event variance included in the straddle.
