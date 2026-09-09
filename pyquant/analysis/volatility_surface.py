from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from pyquant.analysis.option_chain_analysis import OptionChainAnalysis
from pyquant.analysis.volatility_smile import (
    VolatilitySmile,
    build_volatility_smile,
)


@dataclass(frozen=True)
class VolatilitySurface:
    """
    A collection of fitted volatility smiles for one underlying asset.

    Each smile represents the implied-volatility curve for one expiry.
    Together, the smiles form a volatility surface across strike and expiry.
    """

    symbol: str
    spot: float
    smiles: tuple[VolatilitySmile, ...]

    def expiries(self) -> tuple[date, ...]:
        """
        Return all expiries represented by the surface.
        """

        return tuple(smile.expiry for smile in self.smiles)

    def smile_for_expiry(self, expiry: date) -> VolatilitySmile:
        """
        Return the volatility smile for an exact expiry.

        Raises:
            ValueError: If the requested expiry is not in the surface.
        """

        for smile in self.smiles:
            if smile.expiry == expiry:
                return smile

        available_expiries = ", ".join(expiry.isoformat() for expiry in self.expiries())

        raise ValueError(
            f"No volatility smile exists for expiry {expiry}. "
            f"Available expiries: {available_expiries}"
        )

    def nearest_smile(self, expiry: date) -> VolatilitySmile:
        """
        Return the smile whose expiry is closest to the requested expiry.
        """

        if not self.smiles:
            raise ValueError("The volatility surface contains no smiles.")

        return min(
            self.smiles,
            key=lambda smile: abs((smile.expiry - expiry).days),
        )

    def implied_volatility(
        self,
        strike: float,
        expiry: date,
    ) -> float:
        """
        Return fitted implied volatility using the nearest available smile.

        This is an initial implementation. Later, this method can interpolate
        between the smiles immediately before and after the requested expiry.
        """

        smile = self.nearest_smile(expiry)

        return smile.implied_volatility(strike)


def build_volatility_surface(
    analyses: Sequence[OptionChainAnalysis],
    degree: int = 2,
) -> VolatilitySurface:
    """
    Build a volatility surface from option-chain analyses.

    One fitted volatility smile is created for each expiry.

    Args:
        analyses:
            Option-chain analyses for the same underlying asset, with one
            analysis for each expiry.

        degree:
            Polynomial degree used when fitting each volatility smile.

    Returns:
        A VolatilitySurface containing one smile per expiry.

    Raises:
        ValueError:
            If no analyses are supplied, symbols do not match, spots are
            invalid, or multiple analyses have the same expiry.
    """

    if not analyses:
        raise ValueError(
            "At least one option-chain analysis is required "
            "to build a volatility surface."
        )

    symbol = analyses[0].symbol
    spot = analyses[0].spot

    if spot <= 0:
        raise ValueError("Spot price must be positive.")

    smiles: list[VolatilitySmile] = []
    seen_expiries: set[date] = set()

    for analysis in analyses:
        if analysis.symbol != symbol:
            raise ValueError(
                "All option-chain analyses must belong to the same symbol. "
                f"Expected {symbol}, received {analysis.symbol}."
            )

        if analysis.expiry in seen_expiries:
            raise ValueError(
                f"Duplicate analysis supplied for expiry {analysis.expiry}."
            )

        seen_expiries.add(analysis.expiry)

        smile = build_volatility_smile(
            analysis=analysis,
            degree=degree,
        )

        smiles.append(smile)

    smiles.sort(key=lambda smile: smile.expiry)

    return VolatilitySurface(
        symbol=symbol,
        spot=spot,
        smiles=tuple(smiles),
    )
