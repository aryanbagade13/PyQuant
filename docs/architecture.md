# Research architecture

## Data flow

```text
Alpha Vantage earnings -+
                        +-> reviewed event and release timing
Nasdaq timing ----------+                 |
                                          +-> Yahoo adjusted closes -> realised move
                                          |
                                          +-> Alpaca raw stock/option bars
                                                        |
                                                        v
                                              implied move / variance
                                                        |
                                                        v
                                               auditable CSV record
```

External services sit behind small provider interfaces. The calculation and
date-selection tests therefore use in-memory providers and do not require API
keys. Separate live examples check the real integrations.

## Decisions that matter

### Release timing

Before-open events use the previous session's close and the release-day close.
After-close events use the release-day close and the following session's close.
Unknown and during-market-hours events are rejected rather than guessed.

### Point-in-time option inputs

The default observation is 3:55 p.m. New York time, ten valid trading sessions
before the event. Both expiries are observed at that cutoff. Bars after the
cutoff or more than 60 minutes old are rejected.

### Raw and adjusted prices

Option strikes are compared with a contemporaneous raw share price. Realised
returns use adjusted closes so that a corporate action is not mistaken for an
earnings reaction.

### Earnings variance

The short expiry ends before the announcement; the long expiry contains it.
ATM call and put bar closes are inverted to IV and averaged within each expiry.
The short-expiry IV is the current proxy for ordinary volatility:

```text
short total variance = short IV^2 * short time
long total variance  = long IV^2 * long time
ordinary gap variance = short IV^2 * (long time - short time)

raw earnings variance = long total variance
                        - short total variance
                        - ordinary gap variance
```

A negative raw result is retained but the reported implied move uses a zero
floor. The calculation is intentionally simple enough to inspect; it does not
claim to recover a uniquely identifiable event variance.

## Boundaries

`HistoricalEarningsRecord` is the dataset row produced by the first workflow.
`HistoricalEarningsVarianceEstimate` stores the richer two-expiry observation,
including contracts, timestamps, prices, rates, IVs, and source labels.

The command-line workflow is the supported research entry point. The Streamlit
dashboard remains an experimental viewer for current option chains and is not
used to produce the historical result.
