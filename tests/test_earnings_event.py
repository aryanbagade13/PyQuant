from datetime import date

import pytest

from pyquant.event_volatility import (
    EarningsEvent,
    EarningsReleaseTiming,
    EarningsPriceWindow
)


def test_price_window_calculates_positive_event_return():
    window = EarningsPriceWindow(
        pre_event_date=date(2025, 7, 31),
        post_event_date=date(2025, 8, 1),
        pre_event_price=200.0,
        post_event_price=210.0,
    )

    assert window.event_return == pytest.approx(0.05)
    assert window.absolute_event_move == pytest.approx(0.05)


def test_price_window_calculates_negative_event_return():
    window = EarningsPriceWindow(
        pre_event_date=date(2025, 7, 31),
        post_event_date=date(2025, 8, 1),
        pre_event_price=200.0,
        post_event_price=180.0,
    )

    assert window.event_return == pytest.approx(-0.10)
    assert window.absolute_event_move == pytest.approx(0.10)


def test_price_window_rejects_equal_dates():
    with pytest.raises(
            ValueError,
            match="Pre-event date must be before post-event date.",
    ):
        EarningsPriceWindow(
            pre_event_date=date(2025, 7, 31),
            post_event_date=date(2025, 7, 31),
            pre_event_price=200.0,
            post_event_price=210.0,
        )


def test_price_window_rejects_reversed_dates():
    with pytest.raises(
            ValueError,
            match="Pre-event date must be before post-event date.",
    ):
        EarningsPriceWindow(
            pre_event_date=date(2025, 8, 1),
            post_event_date=date(2025, 7, 31),
            pre_event_price=200.0,
            post_event_price=210.0,
        )


def test_price_window_rejects_non_positive_pre_event_price():
    with pytest.raises(
            ValueError,
            match="Pre-event price must be positive.",
    ):
        EarningsPriceWindow(
            pre_event_date=date(2025, 7, 31),
            post_event_date=date(2025, 8, 1),
            pre_event_price=0.0,
            post_event_price=210.0,
        )


def test_price_window_rejects_non_positive_post_event_price():
    with pytest.raises(
            ValueError,
            match="Post-event price must be positive.",

    ):
        EarningsPriceWindow(
            pre_event_date=date(2025, 7, 31),
            post_event_date=date(2025, 8, 1),
            pre_event_price=200.0,
            post_event_price=-10.0,
        )


def test_earnings_event_calculates_surprises_and_move():
    event = EarningsEvent(
        symbol="aapl",
        earnings_date=date(2025, 7, 31),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        estimated_eps=1.43,
        actual_eps=1.52,
        estimated_revenue=89.2,
        actual_revenue=91.0,
        pre_earnings_price=205.10,
        post_earnings_price=216.30,
        pre_earnings_realised_volatility=0.214,
        pre_earnings_implied_volatility=0.348,
    )

    assert event.symbol == "AAPL"

    assert event.eps_surprise == pytest.approx(
        (1.52 - 1.43) / 1.43
    )

    assert event.revenue_surprise == pytest.approx(
        (91.0 - 89.2) / 89.2
    )

    assert event.earnings_return == pytest.approx(
        216.30 / 205.10 - 1.0
    )

    assert event.absolute_earnings_move == pytest.approx(
        abs(216.30 / 205.10 - 1.0)
    )


def test_earnings_event_handles_negative_eps_estimate():
    event = EarningsEvent(
        symbol="TEST",
        earnings_date=date(2025, 7, 31),
        release_timing=EarningsReleaseTiming.BEFORE_MARKET_OPEN,
        estimated_eps=-0.50,
        actual_eps=-0.40,
        estimated_revenue=None,
        actual_revenue=None,
        pre_earnings_price=20.00,
        post_earnings_price=22.00,
    )

    assert event.eps_surprise == pytest.approx(0.20)
    assert event.revenue_surprise is None


def test_earnings_event_returns_none_for_zero_eps_estimate():
    event = EarningsEvent(
        symbol="TEST",
        earnings_date=date(2025, 7, 31),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        estimated_eps=0.0,
        actual_eps=0.10,
        estimated_revenue=100.0,
        actual_revenue=105.0,
        pre_earnings_price=20.00,
        post_earnings_price=21.00,
    )

    assert event.eps_surprise is None

    assert event.revenue_surprise == pytest.approx(
        (105.0 - 100.0) / 100.0
    )


def test_earnings_event_rejects_non_positive_pre_earnings_price():
    with pytest.raises(
            ValueError,
            match="Pre-earnings price must be positive.",
    ):
        EarningsEvent(
            symbol="TEST",
            earnings_date=date(2025, 7, 31),
            release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
            estimated_eps=1.0,
            actual_eps=1.1,
            estimated_revenue=100.0,
            actual_revenue=105.0,
            pre_earnings_price=0.0,
            post_earnings_price=21.0,
        )


def test_earnings_event_rejects_non_positive_post_earnings_price():
    with pytest.raises(
            ValueError,
            match="Post-earnings price must be positive.",
    ):
        EarningsEvent(
            symbol="TEST",
            earnings_date=date(2025, 7, 31),
            release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
            estimated_eps=1.0,
            actual_eps=1.1,
            estimated_revenue=100.0,
            actual_revenue=105.0,
            pre_earnings_price=20.0,
            post_earnings_price=0.0,
        )


def test_earnings_event_rejects_negative_realised_volatility():
    with pytest.raises(
            ValueError,
            match="Realised volatility cannot be negative.",
    ):
        EarningsEvent(
            symbol="TEST",
            earnings_date=date(2025, 7, 31),
            release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
            estimated_eps=1.0,
            actual_eps=1.1,
            estimated_revenue=100.0,
            actual_revenue=105.0,
            pre_earnings_price=20.0,
            post_earnings_price=21.0,
            pre_earnings_realised_volatility=-0.20,
        )


def test_earnings_event_rejects_negative_implied_volatility():
    with pytest.raises(
            ValueError,
            match="Implied volatility cannot be negative.",
    ):
        EarningsEvent(
            symbol="TEST",
            earnings_date=date(2025, 7, 31),
            release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
            estimated_eps=1.0,
            actual_eps=1.1,
            estimated_revenue=100.0,
            actual_revenue=105.0,
            pre_earnings_price=20.0,
            post_earnings_price=21.0,
            pre_earnings_implied_volatility=-0.30,
        )


def test_earnings_event_normalises_symbol():
    event = EarningsEvent(
        symbol=" msft",
        earnings_date=date(2025, 7, 31),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        estimated_eps=2.0,
        actual_eps=2.1,
        estimated_revenue=100.0,
        actual_revenue=101.0,
        pre_earnings_price=50.0,
        post_earnings_price=52.0,
    )

    assert event.symbol == "MSFT"


def test_earnings_event_stores_release_timing():
    event = EarningsEvent(
        symbol="AAPL",
        earnings_date=date(2025, 7, 31),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        estimated_eps=1.43,
        actual_eps=1.52,
        estimated_revenue=89.2,
        actual_revenue=91.0,
        pre_earnings_price=205.10,
        post_earnings_price=216.30,
    )

    assert (
            event.release_timing
            is EarningsReleaseTiming.AFTER_MARKET_CLOSE
    )
