from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.models.earnings_move_comparison import (
    EarningsMoveComparison,
)
from pyquant.event_volatility.earnings_lab.models.earnings_price_window import (
    EarningsPriceWindow,
)


def make_window(post_price: float) -> EarningsPriceWindow:
    return EarningsPriceWindow(
        pre_event_date=date(2025, 1, 30),
        post_event_date=date(2025, 1, 31),
        pre_event_price=100.0,
        post_event_price=post_price,
    )


def test_identifies_an_underestimated_positive_move() -> None:
    comparison = EarningsMoveComparison(
        implied_move=0.04,
        price_window=make_window(106.0),
    )

    assert comparison.realised_return == pytest.approx(0.06)
    assert comparison.realised_move == pytest.approx(0.06)
    assert comparison.move_difference == pytest.approx(0.02)
    assert comparison.realised_to_implied_ratio == pytest.approx(1.5)
    assert comparison.market_assessment == "underestimated"


def test_uses_move_magnitude_for_a_negative_return() -> None:
    comparison = EarningsMoveComparison(
        implied_move=0.05,
        price_window=make_window(97.0),
    )

    assert comparison.realised_return == pytest.approx(-0.03)
    assert comparison.realised_move == pytest.approx(0.03)
    assert comparison.move_difference == pytest.approx(-0.02)
    assert comparison.market_assessment == "overestimated"


def test_zero_implied_move_has_no_ratio() -> None:
    comparison = EarningsMoveComparison(
        implied_move=0.0,
        price_window=make_window(101.0),
    )

    assert comparison.realised_to_implied_ratio is None


@pytest.mark.parametrize("invalid_move", [-0.01, float("nan")])
def test_rejects_invalid_implied_move(invalid_move: float) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        EarningsMoveComparison(
            implied_move=invalid_move,
            price_window=make_window(101.0),
        )
