from datetime import date

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.portfolio.portfolio import Portfolio
from pyquant.portfolio.position import Position


option_1 = EuropeanOption(
    underlying="AAPL",
    strike=200.0,
    expiry=date(2027, 7, 22),
    option_type="call",
)

option_2 = EuropeanOption(
    underlying="AAPL",
    strike=220.0,
    expiry=date(2027, 7, 22),
    option_type="call",
)


quote_1 = OptionQuote(
    option=option_1,
    bid=18.50,
    ask=19.00,
)


quote_2 = OptionQuote(
    option=option_2,
    bid=10.20,
    ask=10.60,
)

position_1 = Position(
    quote=quote_1,
    quantity=10,
)

position_2 = Position(
    quote=quote_2,
    quantity=-5,
)

portfolio = Portfolio()

portfolio.add_position(position_1)
portfolio.add_position(position_2)

market_state = MarketState(
    spot=210.0,
    volatility=0.25,
    risk_free_rate=0.04,
    dividend_yield=0.01,
    valuation_date=date(2026, 7, 22),
)

risk_report = portfolio.risk_report(market_state)
print(portfolio)
print(risk_report)