from dataclasses import dataclass
from datetime import datetime

from pyquant.market.option_quote import OptionQuote


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    spot: float
    timestamp: datetime
    option_quotes: tuple[OptionQuote, ...]

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Symbol cannot be empty.")

        if self.spot <= 0:
            raise ValueError("Spot must be positive.")

    def calls(self) -> tuple[OptionQuote, ...]:
        return tuple(
            quote for quote in self.option_quotes if quote.option.option_type == "call"
        )

    def puts(self) -> tuple[OptionQuote, ...]:
        return tuple(
            quote for quote in self.option_quotes if quote.option.option_type == "put"
        )
