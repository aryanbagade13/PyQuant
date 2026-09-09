from dataclasses import dataclass
from datetime import date

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)


@dataclass(frozen=True)
class EarningsEvent:
    """
    Represents one historical company earnings announcement.

    The estimates must be the analyst consensus values available
    before the announcement. The actual values are the results
    reported by the company.
    """

    symbol: str
    earnings_date: date
    release_timing: EarningsReleaseTiming
    estimated_eps: float | None
    actual_eps: float | None

    estimated_revenue: float | None
    actual_revenue: float | None

    pre_earnings_price: float
    post_earnings_price: float

    pre_earnings_realised_volatility: float | None = None
    pre_earnings_implied_volatility: float | None = None

    def __post_init__(self) -> None:
        normalised_symbol = self.symbol.strip().upper()

        if not normalised_symbol:
            raise ValueError("Symbol cannot be empty.")

        if self.pre_earnings_price <= 0:
            raise ValueError("Pre-earnings price must be positive.")

        if self.post_earnings_price <= 0:
            raise ValueError("Post-earnings price must be positive.")

        if (
            self.pre_earnings_realised_volatility is not None
            and self.pre_earnings_realised_volatility < 0
        ):
            raise ValueError("Realised volatility cannot be negative.")

        if (
            self.pre_earnings_implied_volatility is not None
            and self.pre_earnings_implied_volatility < 0
        ):
            raise ValueError("Implied volatility cannot be negative.")

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

    @property
    def earnings_return(self) -> float:
        """
        Signed return across the earnings event.

        A result of 0.05 means the stock rose by 5%.
        A result of -0.05 means the stock fell by 5%.
        """
        return self.post_earnings_price / self.pre_earnings_price - 1.0

    @property
    def absolute_earnings_move(self) -> float:
        """
        Magnitude of the stock-price move, ignoring direction.
        """
        return abs(self.earnings_return)

    @property
    def eps_surprise(self) -> float | None:
        """
        EPS surprise relative to the magnitude of the estimate.

        Example:
            estimated EPS = 1.00
            actual EPS = 1.10
            EPS surprise = 0.10, meaning 10%
        """
        if (
            self.estimated_eps is None
            or self.actual_eps is None
            or self.estimated_eps == 0
        ):
            return None

        return (self.actual_eps - self.estimated_eps) / abs(self.estimated_eps)

    @property
    def revenue_surprise(self) -> float | None:
        """
        Revenue surprise relative to the estimate.
        """
        if (
            self.estimated_revenue is None
            or self.actual_revenue is None
            or self.estimated_revenue == 0
        ):
            return None

        return (self.actual_revenue - self.estimated_revenue) / abs(
            self.estimated_revenue
        )
