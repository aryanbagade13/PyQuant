from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EarningsReport:
    """
    Raw historical earnings information retrieved from a data provider.

    Unlike EarningsEvent, this object does not yet contain stock prices,
    volatility features, or a confirmed release time.
    """

    symbol: str
    reported_date: date
    fiscal_period_end: date

    estimated_eps: float | None
    actual_eps: float | None

    provider_surprise: float | None = None
    provider_surprise_percentage: float | None = None
    estimated_revenue: float | None = None
    actual_revenue: float | None = None

    def __post_init__(self) -> None:
        normalised_symbol = self.symbol.strip().upper()

        if not normalised_symbol:
            raise ValueError("Symbol cannot be empty.")

        if self.reported_date < self.fiscal_period_end:
            raise ValueError(
                "Reported date cannot be before the fiscal period end."
            )

        object.__setattr__(
            self,
            "symbol",
            normalised_symbol,
        )

    @property
    def calculated_eps_surprise(self) -> float | None:
        """
        EPS surprise relative to the magnitude of the estimate.

        Returns a decimal. For example, 0.10 represents a 10% surprise.
        """
        if (
            self.estimated_eps is None
            or self.actual_eps is None
            or self.estimated_eps == 0
        ):
            return None

        return (
            self.actual_eps - self.estimated_eps
        ) / abs(self.estimated_eps)
