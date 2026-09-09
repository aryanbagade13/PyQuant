from datetime import date
from typing import Protocol

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)


class ReleaseTimingProvider(Protocol):
    """Interface for retrieving an earnings announcement's session timing."""

    def get_release_timing(
        self,
        symbol: str,
        earnings_date: date,
    ) -> EarningsReleaseTiming: ...
