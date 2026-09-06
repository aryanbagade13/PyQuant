from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.price_window_builder import (
    build_earnings_price_window,
)


class FakePriceProvider:
    def __init__(self, prices: dict[date, float]) -> None:
        self.prices = prices
        self.calls: list[tuple[str, date, date]] = []

    def get_historical_closes(
        self, symbol: str, start_date: date, end_date: date
    ) -> dict[date, float]:
        self.calls.append((symbol, start_date, end_date))
        return self.prices


def test_after_close_uses_release_close_and_next_trading_session() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 7, 3): 200,
            # July 4 is a market holiday.
            date(2025, 7, 7): 210,
        }
    )

    window = build_earnings_price_window(
        provider,
        " aapl ",
        date(2025, 7, 3),
        EarningsReleaseTiming.AFTER_MARKET_CLOSE,
    )

    assert window.pre_event_date == date(2025, 7, 3)
    assert window.post_event_date == date(2025, 7, 7)
    assert window.event_return == pytest.approx(0.05)
    assert provider.calls[0][0] == "AAPL"


def test_before_open_uses_previous_and_release_day_sessions() -> None:
    provider = FakePriceProvider(
        {
            date(2025, 1, 17): 100,
            date(2025, 1, 21): 95,
            date(2025, 1, 22): 97,
        }
    )

    window = build_earnings_price_window(
        provider,
        "MSFT",
        date(2025, 1, 21),
        EarningsReleaseTiming.BEFORE_MARKET_OPEN,
    )

    assert window.pre_event_date == date(2025, 1, 17)
    assert window.post_event_date == date(2025, 1, 21)
    assert window.event_return == pytest.approx(-0.05)


@pytest.mark.parametrize(
    "timing",
    [EarningsReleaseTiming.UNKNOWN, EarningsReleaseTiming.DURING_MARKET_HOURS],
)
def test_unsafe_release_timings_are_rejected(timing) -> None:
    with pytest.raises(ValueError):
        build_earnings_price_window(
            FakePriceProvider({}), "AAPL", date(2025, 1, 1), timing
        )


def test_missing_side_of_window_is_rejected() -> None:
    provider = FakePriceProvider({date(2025, 1, 30): 100})
    with pytest.raises(ValueError, match="Insufficient historical prices"):
        build_earnings_price_window(
            provider,
            "AAPL",
            date(2025, 1, 30),
            EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        )
