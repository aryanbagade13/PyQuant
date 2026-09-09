from collections.abc import Iterator
from dataclasses import dataclass, field

from pyquant.market.market_state import MarketState
from pyquant.portfolio.position import Position
from pyquant.portfolio.risk_report import RiskReport


@dataclass
class Portfolio:
    positions: list[Position] = field(default_factory=list)

    def add_position(self, position: Position) -> None:
        self.positions.append(position)

    def remove_position(self, position: Position) -> None:
        self.positions.remove(position)

    def market_value(self) -> float:
        return sum(
            position.quantity * position.quote.mid_price for position in self.positions
        )

    def gross_market_value(self) -> float:
        return sum(
            abs(position.quantity * position.quote.mid_price)
            for position in self.positions
        )

    def liquidation_value(self) -> float:
        total = 0.0

        for position in self.positions:
            if position.quantity > 0:
                total += position.quantity * position.quote.bid
            else:
                total += position.quantity * position.quote.ask

        return total

    def liquidation_cost(self) -> float:
        return self.market_value() - self.liquidation_value()

    def theoretical_value(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.theoretical_value(market) for position in self.positions)

    def delta(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.delta(market) for position in self.positions)

    def gamma(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.gamma(market) for position in self.positions)

    def vega(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.vega(market) for position in self.positions)

    def theta(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.theta(market) for position in self.positions)

    def rho(
        self,
        market: MarketState,
    ) -> float:
        return sum(position.rho(market) for position in self.positions)

    def risk_report(
        self,
        market: MarketState,
    ) -> RiskReport:
        return RiskReport(
            theoretical_value=self.theoretical_value(market),
            delta=self.delta(market),
            gamma=self.gamma(market),
            vega=self.vega(market),
            theta=self.theta(market),
            rho=self.rho(market),
        )

    def __len__(self) -> int:
        return len(self.positions)

    def __iter__(self) -> Iterator[Position]:
        return iter(self.positions)

    def __str__(self) -> str:
        if not self.positions:
            return "Portfolio is empty."

        position_lines = "\n".join(f"  {position}" for position in self.positions)

        return (
            f"Portfolio\n"
            f"{position_lines}\n"
            f"Market value: "
            f"{self.market_value():.2f}\n"
            f"Gross market value: "
            f"{self.gross_market_value():.2f}\n"
            f"Liquidation value: "
            f"{self.liquidation_value():.2f}\n"
            f"Liquidation cost: "
            f"{self.liquidation_cost():.2f}"
        )
