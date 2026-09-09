from dataclasses import dataclass
from math import isfinite

from pyquant.event_volatility.earnings_lab.models.earnings_price_window import (
    EarningsPriceWindow,
)


@dataclass(frozen=True)
class EarningsMoveComparison:
    """Compare a pre-event implied move with the realised event return."""

    implied_move: float
    price_window: EarningsPriceWindow

    def __post_init__(self) -> None:
        if not isfinite(self.implied_move) or self.implied_move < 0:
            raise ValueError("Implied move must be finite and non-negative.")

    @property
    def realised_return(self) -> float:
        return self.price_window.event_return

    @property
    def realised_move(self) -> float:
        return self.price_window.absolute_event_move

    @property
    def move_difference(self) -> float:
        """Realised magnitude minus implied magnitude."""
        return self.realised_move - self.implied_move

    @property
    def realised_to_implied_ratio(self) -> float | None:
        if self.implied_move == 0:
            return None
        return self.realised_move / self.implied_move

    @property
    def market_assessment(self) -> str:
        if self.move_difference > 0:
            return "underestimated"
        if self.move_difference < 0:
            return "overestimated"
        return "matched"
