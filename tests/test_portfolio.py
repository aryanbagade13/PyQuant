from datetime import date

import pytest

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.option_quote import OptionQuote
from pyquant.portfolio.portfolio import Portfolio
from pyquant.portfolio.position import Position


@pytest.fixture
def position_1() -> Position:
    option = EuropeanOption(
        underlying="AAPL",
        strike=200.0,
        expiry=date(2027, 7, 22),
        option_type="call",
    )

    quote = OptionQuote(
        option=option,
        bid=18.50,
        ask=19.00,
    )

    return Position(
        quote=quote,
        quantity=10,
    )


@pytest.fixture
def position_2() -> Position:
    option = EuropeanOption(
        underlying="AAPL",
        strike=220.0,
        expiry=date(2027, 7, 22),
        option_type="call",
    )

    quote = OptionQuote(
        option=option,
        bid=10.20,
        ask=10.60,
    )

    return Position(
        quote=quote,
        quantity=-5,
    )


@pytest.fixture
def portfolio(
    position_1: Position,
    position_2: Position,
) -> Portfolio:
    return Portfolio(
        positions=[position_1, position_2]
    )


def test_portfolio_starts_empty() -> None:
    portfolio = Portfolio()

    assert len(portfolio) == 0
    assert portfolio.market_value() == pytest.approx(0.0)
    assert portfolio.gross_market_value() == pytest.approx(0.0)
    assert portfolio.liquidation_value() == pytest.approx(0.0)
    assert portfolio.liquidation_cost() == pytest.approx(0.0)


def test_portfolio_length(portfolio: Portfolio) -> None:
    assert len(portfolio) == 2


def test_add_position(
    position_1: Position,
) -> None:
    portfolio = Portfolio()

    portfolio.add_position(position_1)

    assert len(portfolio) == 1
    assert portfolio.positions[0] == position_1


def test_remove_position(
    portfolio: Portfolio,
    position_1: Position,
) -> None:
    portfolio.remove_position(position_1)

    assert len(portfolio) == 1
    assert position_1 not in portfolio.positions


def test_portfolio_is_iterable(
    portfolio: Portfolio,
    position_1: Position,
    position_2: Position,
) -> None:
    positions = list(portfolio)

    assert positions == [position_1, position_2]


def test_market_value(portfolio: Portfolio) -> None:
    assert portfolio.market_value() == pytest.approx(135.50)


def test_gross_market_value(portfolio: Portfolio) -> None:
    assert portfolio.gross_market_value() == pytest.approx(239.50)


def test_liquidation_value(portfolio: Portfolio) -> None:
    assert portfolio.liquidation_value() == pytest.approx(132.00)


def test_liquidation_cost(portfolio: Portfolio) -> None:
    assert portfolio.liquidation_cost() == pytest.approx(3.50)


def test_position_quantity_cannot_be_zero(
    position_1: Position,
) -> None:
    with pytest.raises(
        ValueError,
        match="Position quantity cannot be zero.",
    ):
        Position(
            quote=position_1.quote,
            quantity=0,
        )