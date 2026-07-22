from dataclasses import dataclass


@dataclass(frozen=True)
class RiskReport:
    theoretical_value: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float

    @property
    def vega_per_volatility_point(self) -> float:
        return self.vega / 100.0

    @property
    def theta_per_calendar_day(self) -> float:
        return self.theta / 365.0

    @property
    def rho_per_percentage_point(self) -> float:
        return self.rho / 100.0

    def __str__(self) -> str:
        return (
            "Portfolio Risk\n"
            f"Theoretical value: {self.theoretical_value:.2f}\n"
            f"Delta: {self.delta:.4f}\n"
            f"Gamma: {self.gamma:.4f}\n"
            f"Vega: {self.vega:.4f}\n"
            f"Theta: {self.theta:.4f}\n"
            f"Rho: {self.rho:.4f}\n"
            f"Vega per 1 volatility point: "
            f"{self.vega_per_volatility_point:.4f}\n"
            f"Theta per calendar day: "
            f"{self.theta_per_calendar_day:.4f}\n"
            f"Rho per 1 percentage point: "
            f"{self.rho_per_percentage_point:.4f}"
        )