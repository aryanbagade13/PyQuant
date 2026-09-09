from dataclasses import dataclass
from datetime import datetime

from pyquant.instruments.european_option import EuropeanOption


@dataclass(frozen=True)
class OptionQuote:
    option: EuropeanOption
    bid: float
    ask: float
    last_price: float | None = None
    last_trade_time: datetime | None = None

    @property
    def mid_price(self) -> float:
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2

        if self.last_price is not None and self.last_price > 0:
            return self.last_price

        raise ValueError("No valid midpoint or last price is available.")

    @property
    def spread(self) -> float | None:
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid

        return None
