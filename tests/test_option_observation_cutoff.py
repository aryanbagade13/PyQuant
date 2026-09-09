from datetime import date, time

import pytest

from pyquant.event_volatility.earnings_lab.calculations.option_observation_cutoff import (
    select_option_observation_cutoff,
)
from pyquant.event_volatility.earnings_lab.calculations.pre_earnings_cutoff import (
    NEW_YORK,
)
from pyquant.event_volatility.earnings_lab.earnings_expiry_window import (
    EarningsExpiryWindow,
)


class FakePriceProvider:
    def __init__(self, prices: dict[date, float | None]) -> None:
        self.prices = prices
        self.calls: list[tuple[str, date, date]] = []

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float | None]:
        self.calls.append((symbol, start_date, end_date))
        return self.prices


def test_selects_requested_trading_session_and_skips_market_holiday() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 7, 2): 200,
            date(2025, 7, 3): 201,
            # July 4 is absent because the US market was closed.
            date(2025, 7, 7): 202,
            date(2025, 7, 8): 203,
            date(2025, 7, 9): 204,
            date(2025, 7, 10): 205,
            date(2025, 7, 11): 206,
            date(2025, 7, 14): 207,
        }
    )

    cutoff = select_option_observation_cutoff(
        provider=provider,
        symbol=" aapl ",
        earnings_date=date(2025, 7, 15),
        expiry_window=EarningsExpiryWindow(
            short_expiry=date(2025, 7, 11),
            long_expiry=date(2025, 7, 18),
        ),
        trading_sessions_before_earnings=4,
    )

    assert cutoff.date() == date(2025, 7, 9)
    assert cutoff.timetz() == time(15, 55, tzinfo=NEW_YORK)
    assert provider.calls == [("AAPL", date(2025, 5, 31), date(2025, 7, 14))]


def test_ignores_invalid_prices_when_identifying_sessions() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 7, 7): 200,
            date(2025, 7, 8): float("nan"),
            date(2025, 7, 9): 0,
            date(2025, 7, 10): 203,
            date(2025, 7, 11): 204,
        }
    )

    cutoff = select_option_observation_cutoff(
        provider,
        "MSFT",
        date(2025, 7, 15),
        EarningsExpiryWindow(
            short_expiry=date(2025, 7, 14),
            long_expiry=date(2025, 7, 18),
        ),
        trading_sessions_before_earnings=2,
    )

    assert cutoff.date() == date(2025, 7, 10)


def test_rejects_horizon_after_short_expiry() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 7, 28): 200,
            date(2025, 7, 29): 201,
            date(2025, 7, 30): 202,
        }
    )

    with pytest.raises(ValueError, match="is not before the short expiry"):
        select_option_observation_cutoff(
            provider,
            "AAPL",
            date(2025, 7, 31),
            EarningsExpiryWindow(
                short_expiry=date(2025, 7, 25),
                long_expiry=date(2025, 8, 1),
            ),
            trading_sessions_before_earnings=1,
        )


def test_rejects_insufficient_trading_history() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 7, 10): 200,
            date(2025, 7, 11): 201,
        }
    )

    with pytest.raises(ValueError, match="2 valid trading sessions"):
        select_option_observation_cutoff(
            provider,
            "AAPL",
            date(2025, 7, 15),
            EarningsExpiryWindow(
                short_expiry=date(2025, 7, 14),
                long_expiry=date(2025, 7, 18),
            ),
            trading_sessions_before_earnings=3,
        )


@pytest.mark.parametrize(
    ("symbol", "sessions", "search_days", "message"),
    [
        (" ", 10, 45, "Symbol cannot be empty"),
        ("AAPL", 0, 45, "Trading sessions before earnings must be positive"),
        ("AAPL", 10, 0, "Search days must be positive"),
    ],
)
def test_rejects_invalid_configuration(
    symbol: str,
    sessions: int,
    search_days: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        select_option_observation_cutoff(
            FakePriceProvider({}),
            symbol,
            date(2025, 7, 15),
            EarningsExpiryWindow(
                short_expiry=date(2025, 7, 18),
                long_expiry=date(2025, 7, 25),
            ),
            trading_sessions_before_earnings=sessions,
            search_days=search_days,
        )
