from datetime import date
from typing import Protocol

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.models.implied_move import ImpliedMove


class HistoricalImpliedMoveProvider(Protocol):
    def get_implied_move(
        self,
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
        spot: float,
    ) -> ImpliedMove:
        ...
