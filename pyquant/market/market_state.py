from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MarketState:
    spot: float
    volatility: float
    risk_free_rate: float
    dividend_yield: float
    valuation_date: date

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("Spot price must be positive.")
        if self.volatility < 0:
            raise ValueError("Volatility cannot be negative.")
