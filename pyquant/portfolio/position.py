from dataclasses import dataclass
from dataclasses import replace

from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.pricing.black_scholes import black_scholes_price
from pyquant.pricing.greeks import (
    delta as option_delta,
    gamma as option_gamma,
    vega as option_vega,
    theta as option_theta,
    rho as option_rho,
)


@dataclass(frozen=True)
class Position:
    quote: OptionQuote
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity == 0:
            raise ValueError(
                "Position quantity cannot be zero."
            )

    def theoretical_value(
            self,
            market: MarketState,
    ) -> float:
        option_price = black_scholes_price(
            option=self.quote.option,
            market=market,
        )

        return self.quantity * option_price

    def delta(
            self,
            market: MarketState,
    ) -> float:
        return self.quantity * option_delta(
            option=self.quote.option,
            market=market,
        )

    def gamma(
            self,
            market: MarketState,
    ) -> float:
        return self.quantity * option_gamma(
            option=self.quote.option,
            market=market,
        )

    def vega(
            self,
            market: MarketState,
    ) -> float:
        return self.quantity * option_vega(
            option=self.quote.option,
            market=market,
        )

    def theta(
            self,
            market: MarketState,
    ) -> float:
        return self.quantity * option_theta(
            option=self.quote.option,
            market=market,
        )

    def rho(
            self,
            market: MarketState,
    ) -> float:
        return self.quantity * option_rho(
            option=self.quote.option,
            market=market,
        )

    def __str__(self) -> str:
        option = self.quote.option
        direction = "Long" if self.quantity > 0 else "Short"

        return (
            f"{direction} {abs(self.quantity)} "
            f"{option.underlying} {option.option_type} "
            f"K={option.strike:.2f}, "
            f"expiry={option.expiry}, "
            f"mid={self.quote.mid_price:.2f}"
        )
