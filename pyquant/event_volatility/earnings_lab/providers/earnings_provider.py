from typing import Protocol

from pyquant.event_volatility.earnings_lab.models.earnings_report import (
    EarningsReport,
)


class EarningsProvider(Protocol):
    """Interface implemented by historical earnings data sources."""

    def get_historical_earnings(self, symbol: str) -> list[EarningsReport]:
        """Return historical reports ordered from oldest to newest."""
        ...
