import math

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.pricing.maths import calculate_d1, calculate_d2, normal_cdf, normal_pdf
from pyquant.pricing.time import time_to_expiry


def delta(
    option: EuropeanOption,
    market: MarketState,
) -> float:
    spot = market.spot
    strike = option.strike
    volatility = market.volatility
    risk_free_rate = market.risk_free_rate
    dividend_yield = market.dividend_yield

    time_to_expiry_value = time_to_expiry(
        expiry=option.expiry,
        valuation_date=market.valuation_date,
    )

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry_value,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    dividend_discount_factor = math.exp(-dividend_yield * time_to_expiry_value)

    if option.option_type == "call":
        return dividend_discount_factor * normal_cdf(d1)

    return dividend_discount_factor * (normal_cdf(d1) - 1.0)


def gamma(
    option: EuropeanOption,
    market: MarketState,
) -> float:
    spot = market.spot
    strike = option.strike
    volatility = market.volatility
    risk_free_rate = market.risk_free_rate
    dividend_yield = market.dividend_yield

    time_to_expiry_value = time_to_expiry(
        expiry=option.expiry,
        valuation_date=market.valuation_date,
    )

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry_value,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    dividend_discount_factor = math.exp(-dividend_yield * time_to_expiry_value)

    return (
        dividend_discount_factor
        * normal_pdf(d1)
        / (spot * volatility * math.sqrt(time_to_expiry_value))
    )


def vega(
    option: EuropeanOption,
    market: MarketState,
) -> float:
    spot = market.spot
    strike = option.strike
    volatility = market.volatility
    risk_free_rate = market.risk_free_rate
    dividend_yield = market.dividend_yield

    time_to_expiry_value = time_to_expiry(
        expiry=option.expiry,
        valuation_date=market.valuation_date,
    )

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry_value,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    dividend_discount_factor = math.exp(-dividend_yield * time_to_expiry_value)

    return (
        spot
        * dividend_discount_factor
        * normal_pdf(d1)
        * math.sqrt(time_to_expiry_value)
    )


def theta(
    option: EuropeanOption,
    market: MarketState,
) -> float:
    spot = market.spot
    strike = option.strike
    volatility = market.volatility
    risk_free_rate = market.risk_free_rate
    dividend_yield = market.dividend_yield

    time_to_expiry_value = time_to_expiry(
        expiry=option.expiry,
        valuation_date=market.valuation_date,
    )

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry_value,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    d2 = calculate_d2(
        d1=d1,
        volatility=volatility,
        time_to_expiry=time_to_expiry_value,
    )

    dividend_discount_factor = math.exp(-dividend_yield * time_to_expiry_value)

    risk_free_discount_factor = math.exp(-risk_free_rate * time_to_expiry_value)

    first_term = (
        -spot
        * dividend_discount_factor
        * normal_pdf(d1)
        * volatility
        / (2.0 * math.sqrt(time_to_expiry_value))
    )

    if option.option_type == "call":
        return (
            first_term
            - dividend_yield * spot * dividend_discount_factor * normal_cdf(d1)
            + risk_free_rate * strike * risk_free_discount_factor * normal_cdf(d2)
        )

    return (
        first_term
        + dividend_yield * spot * dividend_discount_factor * normal_cdf(-d1)
        - risk_free_rate * strike * risk_free_discount_factor * normal_cdf(-d2)
    )


def rho(
    option: EuropeanOption,
    market: MarketState,
) -> float:
    strike = option.strike
    volatility = market.volatility
    risk_free_rate = market.risk_free_rate
    dividend_yield = market.dividend_yield
    spot = market.spot

    time_to_expiry_value = time_to_expiry(
        expiry=option.expiry,
        valuation_date=market.valuation_date,
    )

    d1 = calculate_d1(
        spot=spot,
        strike=strike,
        time_to_expiry=time_to_expiry_value,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    d2 = calculate_d2(
        d1=d1,
        volatility=volatility,
        time_to_expiry=time_to_expiry_value,
    )

    risk_free_discount_factor = math.exp(-risk_free_rate * time_to_expiry_value)

    if option.option_type == "call":
        return (
            strike * time_to_expiry_value * risk_free_discount_factor * normal_cdf(d2)
        )

    return -strike * time_to_expiry_value * risk_free_discount_factor * normal_cdf(-d2)
