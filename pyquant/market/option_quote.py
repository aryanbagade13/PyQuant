from dataclasses import dataclass

from pyquant.instruments.european_option import EuropeanOption


@dataclass(frozen=True)
class OptionQuote:
    option: EuropeanOption
    bid: float
    ask: float

    def __post_init__(self) -> None:
        if self.bid < 0:
            raise ValueError("Bid cannot be negative.")

        if self.ask < 0:
            raise ValueError("Ask cannot be negative.")

        if self.ask < self.bid:
            raise ValueError("Ask cannot be lower than bid.")

    @property
    def mid_price(self) -> float:
        return (self.bid + self.ask) / 2.0