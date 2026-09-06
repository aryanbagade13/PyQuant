from datetime import date
from typing import Protocol


class HistoricalPriceProvider(Protocol):
    """Interface for retrieving adjusted daily closing prices."""

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        """Return trading-date to adjusted-close mappings, inclusive."""
        ...
