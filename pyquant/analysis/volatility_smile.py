from dataclasses import dataclass

import numpy as np
from numpy.polynomial import Polynomial

from pyquant.analysis.option_chain_analysis import (
    OptionAnalysisRow,
    OptionChainAnalysis,
)


@dataclass(frozen=True)
class VolatilitySmile:
    symbol: str
    spot: float
    expiry: object
    strikes: tuple[float, ...]
    observed_ivs: tuple[float, ...]
    fitted_curve: Polynomial

    def implied_volatility(self, strike: float) -> float:
        """
        Return the fitted implied volatility for a given strike.

        The result is returned as a decimal:
        0.30 means 30%.
        """
        fitted_iv = float(self.fitted_curve(strike))

        if fitted_iv <= 0:
            raise ValueError(
                f"Fitted implied volatility is non-positive at strike {strike}."
            )

        return fitted_iv

    def fitted_points(
        self,
        number_of_points: int = 200,
    ) -> tuple[np.ndarray, np.ndarray]:
        if number_of_points < 2:
            raise ValueError("number_of_points must be at least 2.")

        strike_grid = np.linspace(
            min(self.strikes),
            max(self.strikes),
            number_of_points,
        )

        fitted_ivs = self.fitted_curve(strike_grid)
        return strike_grid, fitted_ivs


def _is_valid_row(
    row: OptionAnalysisRow,
    maximum_relative_spread: float,
    minimum_moneyness: float,
    maximum_moneyness: float,
    minimum_iv: float,
    maximum_iv: float,
) -> bool:
    if row.mid_price <= 0:
        return False

    if row.spread is None:
        return True

    relative_spread = row.spread / row.mid_price

    return (
        relative_spread <= maximum_relative_spread
        and minimum_moneyness <= row.moneyness <= maximum_moneyness
        and minimum_iv <= row.implied_volatility <= maximum_iv
    )


def build_volatility_smile(
    analysis: OptionChainAnalysis,
    degree: int = 2,
    maximum_relative_spread: float = 0.50,
    minimum_moneyness: float = 0.90,
    maximum_moneyness: float = 1.10,
    minimum_iv: float = 0.05,
    maximum_iv: float = 1.00,
) -> VolatilitySmile:
    valid_rows = [
        row
        for row in analysis.rows
        if _is_valid_row(
            row=row,
            maximum_relative_spread=maximum_relative_spread,
            minimum_moneyness=minimum_moneyness,
            maximum_moneyness=maximum_moneyness,
            minimum_iv=minimum_iv,
            maximum_iv=maximum_iv,
        )
    ]

    if len(valid_rows) <= degree:
        raise ValueError(
            "Not enough valid option quotes to fit the volatility smile. "
            f"Need at least {degree + 1}, received {len(valid_rows)}."
        )

    valid_rows.sort(key=lambda row: row.strike)

    strikes = np.array(
        [row.strike for row in valid_rows],
        dtype=float,
    )

    observed_ivs = np.array(
        [row.implied_volatility for row in valid_rows],
        dtype=float,
    )

    fitted_curve = Polynomial.fit(
        x=strikes,
        y=observed_ivs,
        deg=degree,
    )

    return VolatilitySmile(
        symbol=analysis.symbol,
        spot=analysis.spot,
        expiry=analysis.expiry,
        strikes=tuple(strikes),
        observed_ivs=tuple(observed_ivs),
        fitted_curve=fitted_curve,
    )
