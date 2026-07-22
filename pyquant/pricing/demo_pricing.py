from datetime import date

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.pricing.black_scholes import black_scholes_price
from pyquant.pricing.greeks import delta, gamma, vega, theta, rho


option = EuropeanOption(
    underlying="AAPL",
    strike=100.0,
    expiry=date(2027, 7, 21),
    option_type="call",
)

market = MarketState(
    spot=100.0,
    volatility=0.20,
    risk_free_rate=0.05,
    dividend_yield=0.0,
    valuation_date=date(2026, 7, 21),
)

price = black_scholes_price(
    option=option,
    market=market,
)

option_delta = delta(
    option=option,
    market=market,
)

option_gamma = gamma(
    option=option,
    market=market,
)

option_vega = vega(
    option=option,
    market=market,
)

option_theta = theta(
    option=option,
    market=market
)

option_rho = rho(
    option=option,
    market=market
)


print(f"Gamma: {option_gamma:.4f}")
print(f"Option price: {price:.4f}")
print(f"Delta: {option_delta:.4f}")
print(f"Vega: {option_vega:.4f}")
print(f"Theta: {option_theta:.4f}")
print(f"Theta per day: {option_theta / 365.0:.4f}")
print(f"Rho: {option_rho:.4f}")
print(f"Rho per 1% rate change: {option_rho / 100.0:.4f}")