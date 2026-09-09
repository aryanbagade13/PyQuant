from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite

from pyquant.event_volatility.earnings_lab.models.earnings_variance import (
    EarningsVariance,
)


@dataclass(frozen=True)
class HistoricalEarningsVarianceEstimate:
    """Auditable historical inputs and output for one earnings estimate."""

    symbol: str
    observation_time: datetime
    spot: float
    spot_observation_time: datetime
    risk_free_rate: float
    dividend_yield: float

    short_atm_strike: float
    short_call_symbol: str
    short_put_symbol: str
    short_call_price: float
    short_put_price: float
    short_call_iv: float
    short_put_iv: float
    short_call_observation_time: datetime
    short_put_observation_time: datetime

    long_atm_strike: float
    long_call_symbol: str
    long_put_symbol: str
    long_call_price: float
    long_put_price: float
    long_call_iv: float
    long_put_iv: float
    long_call_observation_time: datetime
    long_put_observation_time: datetime

    decomposition: EarningsVariance
    source: str

    def __post_init__(self) -> None:
        normalised_symbol = self.symbol.strip().upper()
        if not normalised_symbol:
            raise ValueError("Symbol cannot be empty.")
        if self.observation_time.tzinfo is None:
            raise ValueError("Observation time must be timezone-aware.")
        if self.spot_observation_time.tzinfo is None:
            raise ValueError("Spot observation time must be timezone-aware.")
        if self.spot_observation_time > self.observation_time:
            raise ValueError("Spot observation cannot be after the cutoff.")
        if not isfinite(self.risk_free_rate) or not isfinite(self.dividend_yield):
            raise ValueError("Rates must be finite.")

        positive_values = (
            self.spot,
            self.short_atm_strike,
            self.short_call_price,
            self.short_put_price,
            self.long_atm_strike,
            self.long_call_price,
            self.long_put_price,
        )
        if any(not isfinite(value) or value <= 0 for value in positive_values):
            raise ValueError("Spot, strikes, and option prices must be positive.")

        volatility_values = (
            self.short_call_iv,
            self.short_put_iv,
            self.long_call_iv,
            self.long_put_iv,
        )
        if any(not isfinite(value) or value < 0 for value in volatility_values):
            raise ValueError(
                "Historical implied volatilities must be finite and non-negative."
            )

        if not all(
            value.strip()
            for value in (
                self.short_call_symbol,
                self.short_put_symbol,
                self.long_call_symbol,
                self.long_put_symbol,
                self.source,
            )
        ):
            raise ValueError("Contract symbols and source cannot be empty.")

        option_times = (
            self.short_call_observation_time,
            self.short_put_observation_time,
            self.long_call_observation_time,
            self.long_put_observation_time,
        )
        if any(value.tzinfo is None for value in option_times):
            raise ValueError("Option observation times must be timezone-aware.")
        if any(value > self.observation_time for value in option_times):
            raise ValueError("Option observations cannot be after the cutoff.")

        if self.decomposition.valuation_date != self.observation_time.date():
            raise ValueError("Variance valuation date must match the observation date.")
        if (
            self.decomposition.short_implied_volatility != self.short_atm_iv
            or self.decomposition.long_implied_volatility != self.long_atm_iv
        ):
            raise ValueError(
                "Variance inputs must match the historical ATM volatilities."
            )

        object.__setattr__(self, "symbol", normalised_symbol)

    @property
    def short_atm_iv(self) -> float:
        return (self.short_call_iv + self.short_put_iv) / 2.0

    @property
    def long_atm_iv(self) -> float:
        return (self.long_call_iv + self.long_put_iv) / 2.0

    @property
    def short_expiry(self) -> date:
        return self.decomposition.short_expiry

    @property
    def long_expiry(self) -> date:
        return self.decomposition.long_expiry

    @property
    def ordinary_implied_volatility(self) -> float:
        return self.decomposition.ordinary_implied_volatility

    @property
    def earnings_variance(self) -> float:
        return self.decomposition.earnings_variance

    @property
    def earnings_implied_move(self) -> float:
        return self.decomposition.earnings_implied_move
