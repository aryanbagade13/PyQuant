from dataclasses import dataclass
from datetime import date
from math import isfinite, sqrt


@dataclass(frozen=True)
class EarningsVariance:
    """Result of separating ordinary variance from earnings variance."""

    valuation_date: date
    short_expiry: date
    long_expiry: date
    short_implied_volatility: float
    long_implied_volatility: float
    ordinary_implied_volatility: float
    short_total_variance: float
    long_total_variance: float
    incremental_variance: float
    ordinary_variance_between_expiries: float
    raw_earnings_variance: float
    earnings_variance: float

    def __post_init__(self) -> None:
        if not self.valuation_date < self.short_expiry < self.long_expiry:
            raise ValueError("Expected valuation date < short expiry < long expiry.")

        volatility_values = (
            self.short_implied_volatility,
            self.long_implied_volatility,
            self.ordinary_implied_volatility,
        )
        if any(not isfinite(value) or value < 0 for value in volatility_values):
            raise ValueError("Implied volatilities must be finite and non-negative.")

        non_negative_variances = (
            self.short_total_variance,
            self.long_total_variance,
            self.ordinary_variance_between_expiries,
            self.earnings_variance,
        )
        if any(not isfinite(value) or value < 0 for value in non_negative_variances):
            raise ValueError("Calculated variances must be finite and non-negative.")

        signed_variances = (
            self.incremental_variance,
            self.raw_earnings_variance,
        )
        if any(not isfinite(value) for value in signed_variances):
            raise ValueError("Calculated variances must be finite.")

    @property
    def earnings_implied_move(self) -> float:
        """One-off standard-deviation move implied by earnings variance."""
        return sqrt(self.earnings_variance)

    @property
    def was_floored(self) -> bool:
        """Whether the raw estimate was negative and therefore set to zero."""
        return self.raw_earnings_variance < 0
