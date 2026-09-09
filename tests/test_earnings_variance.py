from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.calculations.earnings_variance import (
    decompose_earnings_variance,
)
from pyquant.event_volatility.earnings_lab.earnings_expiry_window import (
    EarningsExpiryWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)


class FakeExpiryProvider:
    def __init__(self, expiries: list[date]) -> None:
        self.expiries = expiries

    def get_expiries(self, symbol: str) -> list[date]:
        return self.expiries


def test_after_close_selects_expiries_on_either_side_of_event() -> None:
    window = EarningsExpiryWindow.from_provider(
        FakeExpiryProvider(
            [
                date(2026, 7, 10),
                date(2026, 7, 17),
                date(2026, 7, 24),
            ]
        ),
        "AAPL",
        date(2026, 7, 17),
        EarningsReleaseTiming.AFTER_MARKET_CLOSE,
    )

    assert window.short_expiry == date(2026, 7, 17)
    assert window.long_expiry == date(2026, 7, 24)


def test_before_open_treats_event_date_expiry_as_long() -> None:
    window = EarningsExpiryWindow.from_provider(
        FakeExpiryProvider(
            [
                date(2026, 7, 10),
                date(2026, 7, 17),
                date(2026, 7, 24),
            ]
        ),
        "AAPL",
        date(2026, 7, 17),
        EarningsReleaseTiming.BEFORE_MARKET_OPEN,
    )

    assert window.short_expiry == date(2026, 7, 10)
    assert window.long_expiry == date(2026, 7, 17)


def test_decomposition_separates_ordinary_and_earnings_variance() -> None:
    result = decompose_earnings_variance(
        valuation_date=date(2026, 7, 3),
        expiry_window=EarningsExpiryWindow(
            short_expiry=date(2026, 7, 10),
            long_expiry=date(2026, 7, 17),
        ),
        short_implied_volatility=0.30,
        long_implied_volatility=0.45,
    )

    short_variance = 0.30**2 * 7 / 365
    long_variance = 0.45**2 * 14 / 365
    ordinary_gap_variance = 0.30**2 * 7 / 365
    expected_earnings_variance = long_variance - short_variance - ordinary_gap_variance

    assert result.short_total_variance == pytest.approx(short_variance)
    assert result.long_total_variance == pytest.approx(long_variance)
    assert result.incremental_variance == pytest.approx(long_variance - short_variance)
    assert result.ordinary_variance_between_expiries == pytest.approx(
        ordinary_gap_variance
    )
    assert result.earnings_variance == pytest.approx(expected_earnings_variance)
    assert result.earnings_implied_move == pytest.approx(
        expected_earnings_variance**0.5
    )
    assert result.earnings_implied_move == pytest.approx(0.06569, abs=0.00001)
    assert result.was_floored is False


def test_decomposition_accepts_a_separate_ordinary_volatility() -> None:
    result = decompose_earnings_variance(
        valuation_date=date(2026, 7, 3),
        expiry_window=EarningsExpiryWindow(
            short_expiry=date(2026, 7, 10),
            long_expiry=date(2026, 7, 17),
        ),
        short_implied_volatility=0.30,
        long_implied_volatility=0.45,
        ordinary_implied_volatility=0.25,
    )

    assert result.ordinary_implied_volatility == pytest.approx(0.25)
    assert result.ordinary_variance_between_expiries == pytest.approx(0.25**2 * 7 / 365)


def test_negative_earnings_variance_is_preserved_but_floored() -> None:
    result = decompose_earnings_variance(
        valuation_date=date(2026, 7, 3),
        expiry_window=EarningsExpiryWindow(
            short_expiry=date(2026, 7, 10),
            long_expiry=date(2026, 7, 17),
        ),
        short_implied_volatility=0.30,
        long_implied_volatility=0.25,
    )

    assert result.raw_earnings_variance < 0
    assert result.earnings_variance == 0
    assert result.earnings_implied_move == 0
    assert result.was_floored is True


@pytest.mark.parametrize(
    "invalid_volatility",
    [-0.01, float("nan"), float("inf")],
)
def test_invalid_implied_volatility_is_rejected(
    invalid_volatility: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Implied volatilities must be finite and non-negative.",
    ):
        decompose_earnings_variance(
            valuation_date=date(2026, 7, 3),
            expiry_window=EarningsExpiryWindow(
                short_expiry=date(2026, 7, 10),
                long_expiry=date(2026, 7, 17),
            ),
            short_implied_volatility=invalid_volatility,
            long_implied_volatility=0.45,
        )


def test_short_expiry_must_be_after_valuation_date() -> None:
    with pytest.raises(
        ValueError,
        match="Short expiry must be after the valuation date.",
    ):
        decompose_earnings_variance(
            valuation_date=date(2026, 7, 10),
            expiry_window=EarningsExpiryWindow(
                short_expiry=date(2026, 7, 10),
                long_expiry=date(2026, 7, 17),
            ),
            short_implied_volatility=0.30,
            long_implied_volatility=0.45,
        )
