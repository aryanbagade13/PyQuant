from datetime import date

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.pricing.black_scholes import black_scholes_price
from pyquant.pricing.implied_volatility import implied_volatility


option = EuropeanOption(
    underlying="AAPL",
    strike=100.0,
    expiry=date(2027, 1, 1),
    option_type="call",
)

market = MarketState(
    spot=100.0,
    volatility=0.30,
    risk_free_rate=0.05,
    dividend_yield=0.0,
    valuation_date=date(2026, 1, 1),
)

model_price = black_scholes_price(
    option=option,
    market=market,
)

quote = OptionQuote(
    option=option,
    bid=model_price - 0.01,
    ask=model_price + 0.01,
)

calculated_iv = implied_volatility(
    quote=quote,
    market=market,
)

print(f"Model price: {model_price:.4f}")
print(f"Mid price: {quote.mid_price:.4f}")
print(f"Calculated IV: {calculated_iv:.2%}")