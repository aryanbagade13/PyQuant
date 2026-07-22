from dataclasses import replace

from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.pricing.black_scholes import black_scholes_price
from pyquant.pricing.greeks import vega


def implied_volatility(
        quote: OptionQuote,
        market: MarketState,
        initial_guess: float = 0.20,
        tolerance: float = 1e-6,
        max_iterations: int = 100,
) -> float:
    if initial_guess <= 0.0:
        raise ValueError(
            "Initial volatility guess must be positive."
        )

    volatility_guess = initial_guess

    for _ in range(max_iterations):
        market_with_guess = replace(
            market,
            volatility=volatility_guess,
        )

        model_price = black_scholes_price(
            option=quote.option,
            market=market_with_guess,
        )

        pricing_error = model_price - quote.mid_price

        if abs(pricing_error) < tolerance:
            return volatility_guess

        option_vega = vega(
            option=quote.option,
            market=market_with_guess,
        )

        if abs(option_vega) < 1e-12:
            raise ValueError(
                "Vega is too small to calculate implied volatility."
            )

        volatility_guess = (
            volatility_guess
            - pricing_error / option_vega
        )

        if volatility_guess <= 0.0:
            volatility_guess = 1e-6

    raise ValueError(
        "Implied volatility calculation did not converge."
    )