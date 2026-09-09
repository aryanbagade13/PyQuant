from datetime import date

from pyquant.event_volatility import (
    EarningsExpiryWindow,
    decompose_earnings_variance,
)

window = EarningsExpiryWindow(
    short_expiry=date(2026, 7, 10),
    long_expiry=date(2026, 7, 17),
)

result = decompose_earnings_variance(
    valuation_date=date(2026, 7, 3),
    expiry_window=window,
    short_implied_volatility=0.30,
    long_implied_volatility=0.45,
)

print(f"Ordinary implied volatility: {result.ordinary_implied_volatility:.2%}")
print(f"Earnings variance: {result.earnings_variance:.6f}")
print(f"Earnings implied move: {result.earnings_implied_move:.2%}")
