import math

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.pricing.time import time_to_expiry


def normal_cdf(x: float) -> float:
    return 0.5 * (
            1.0
            + math.erf(x / math.sqrt(2.0))
    )


def calculate_d1(
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float,
) -> float:
    numerator = (
            math.log(spot / strike)
            + (
                    risk_free_rate
                    - dividend_yield
                    + 0.5 * volatility ** 2
            )
            * time_to_expiry
    )

    denominator = (
            volatility
            * math.sqrt(time_to_expiry)
    )

    return numerator / denominator


def calculate_d2(
        d1: float,
        volatility: float,
        time_to_expiry: float,
) -> float:
    return (
            d1
            - volatility
            * math.sqrt(time_to_expiry)
    )


def black_scholes_price(
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

    if time_to_expiry_value == 0:
        if option.option_type == "call":
            return max(spot - strike, 0.0)

        return max(strike - spot, 0.0)

    if volatility == 0:
        discounted_spot = (
            spot
            * math.exp(
                -dividend_yield
                * time_to_expiry_value
            )
        )

        discounted_strike = (
            strike
            * math.exp(
                -risk_free_rate
                * time_to_expiry_value
            )
        )

        if option.option_type == "call":
            return max(
                discounted_spot - discounted_strike,
                0.0,
            )

        return max(
            discounted_strike - discounted_spot,
            0.0,
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

    if option.option_type == "call":
        return (
                spot
                * math.exp(
                    -dividend_yield
                    * time_to_expiry_value
                )
                * normal_cdf(d1)
                - strike
                * math.exp(
                    -risk_free_rate
                    * time_to_expiry_value
                )
                * normal_cdf(d2)
        )

    return (
            strike
            * math.exp(
                -risk_free_rate
                * time_to_expiry_value
            )
            * normal_cdf(-d2)
            - spot
            * math.exp(
                -dividend_yield
                * time_to_expiry_value
            )
            * normal_cdf(-d1)
    )
