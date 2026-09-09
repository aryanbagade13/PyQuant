from datetime import date
from math import isfinite

from pyquant.event_volatility.earnings_lab.earnings_expiry_window import (
    EarningsExpiryWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_variance import (
    EarningsVariance,
)
from pyquant.pricing.time import time_to_expiry


def decompose_earnings_variance(
    valuation_date: date,
    expiry_window: EarningsExpiryWindow,
    short_implied_volatility: float,
    long_implied_volatility: float,
    ordinary_implied_volatility: float | None = None,
) -> EarningsVariance:
    """
    Separate ordinary variance from the variance attributed to earnings.

    Both implied volatilities must be observed at the same pre-earnings
    timestamp. The short expiry must not contain the announcement, while the
    long expiry must contain it.

    Total variance is ``implied_volatility ** 2 * time_to_expiry``. The
    incremental variance between expiries contains both ordinary variance and
    the earnings jump. Ordinary variance over that gap is subtracted to obtain
    the earnings estimate.

    If no separate ordinary-volatility estimate is supplied, the short-expiry
    implied volatility is used. A negative event estimate is floored at zero,
    while ``raw_earnings_variance`` preserves the value for diagnostics.
    """
    volatility_values = (
        short_implied_volatility,
        long_implied_volatility,
    )
    if any(not isfinite(value) or value < 0 for value in volatility_values):
        raise ValueError("Implied volatilities must be finite and non-negative.")

    if ordinary_implied_volatility is None:
        ordinary_implied_volatility = short_implied_volatility
    elif not isfinite(ordinary_implied_volatility) or ordinary_implied_volatility < 0:
        raise ValueError("Ordinary implied volatility must be finite and non-negative.")

    short_time = time_to_expiry(
        expiry_window.short_expiry,
        valuation_date,
    )
    long_time = time_to_expiry(
        expiry_window.long_expiry,
        valuation_date,
    )
    if short_time <= 0:
        raise ValueError("Short expiry must be after the valuation date.")
    if long_time <= short_time:
        raise ValueError("Long expiry must be after the short expiry.")

    short_total_variance = short_implied_volatility**2 * short_time
    long_total_variance = long_implied_volatility**2 * long_time
    incremental_variance = long_total_variance - short_total_variance

    time_between_expiries = long_time - short_time
    ordinary_variance_between_expiries = (
        ordinary_implied_volatility**2 * time_between_expiries
    )
    raw_earnings_variance = incremental_variance - ordinary_variance_between_expiries
    earnings_variance = max(0.0, raw_earnings_variance)

    return EarningsVariance(
        valuation_date=valuation_date,
        short_expiry=expiry_window.short_expiry,
        long_expiry=expiry_window.long_expiry,
        short_implied_volatility=short_implied_volatility,
        long_implied_volatility=long_implied_volatility,
        ordinary_implied_volatility=ordinary_implied_volatility,
        short_total_variance=short_total_variance,
        long_total_variance=long_total_variance,
        incremental_variance=incremental_variance,
        ordinary_variance_between_expiries=(ordinary_variance_between_expiries),
        raw_earnings_variance=raw_earnings_variance,
        earnings_variance=earnings_variance,
    )
