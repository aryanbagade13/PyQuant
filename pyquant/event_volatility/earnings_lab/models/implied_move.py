from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ImpliedMove:
    """
    Represents the options market's implied move around an event.

    The implied move is approximated using the cost of an
    at-the-money straddle divided by spot.
    """

    spot: float
    atm_strike: float
    call_mid: float
    put_mid: float
    expiry: date | None = None
    call_symbol: str | None = None
    put_symbol: str | None = None
    call_observation_time: datetime | None = None
    put_observation_time: datetime | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if self.spot <= 0:
            raise ValueError("Spot price must be positive.")

        if self.atm_strike <= 0:
            raise ValueError("ATM strike must be positive.")

        if self.call_mid < 0:
            raise ValueError("Call midpoint cannot be negative.")

        if self.put_mid < 0:
            raise ValueError("Put midpoint cannot be negative.")

    @property
    def straddle_price(self) -> float:
        """
        Total cost of buying the ATM call and ATM put.
        """
        return self.call_mid + self.put_mid

    @property
    def implied_move_pct(self) -> float:
        """
        Approximate percentage move implied by the ATM straddle.

        Example:
            spot = 100
            straddle = 6

            implied move = 6 / 100 = 0.06 = 6%
        """
        return self.straddle_price / self.spot
