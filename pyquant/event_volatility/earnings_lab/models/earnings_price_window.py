from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EarningsPriceWindow:
    """
    Defines the prices used to measure the stock-market reaction
    to an earnings announcement.
    """

    pre_event_date: date
    post_event_date: date
    pre_event_price: float
    post_event_price: float

    def __post_init__(self) -> None:
        if self.pre_event_date >= self.post_event_date:
            raise ValueError("Pre-event date must be before post-event date.")

        if self.pre_event_price <= 0:
            raise ValueError("Pre-event price must be positive.")

        if self.post_event_price <= 0:
            raise ValueError("Post-event price must be positive.")

    @property
    def event_return(self) -> float:
        """
        Signed return across the earnings event.
        """
        return self.post_event_price / self.pre_event_price - 1.0

    @property
    def absolute_event_move(self) -> float:
        """
        Magnitude of the event return, ignoring direction.
        """
        return abs(self.event_return)
