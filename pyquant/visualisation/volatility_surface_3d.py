from datetime import date

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from pyquant.analysis.volatility_surface import VolatilitySurface


def plot_volatility_surface(
    surface: VolatilitySurface,
    minimum_moneyness: float = 0.90,
    maximum_moneyness: float = 1.10,
    number_of_strikes: int = 100,
) -> Figure:
    """
    Plot a fitted implied-volatility surface.

    Axes:
        x: moneyness, calculated as strike / spot
        y: days to expiry
        z: implied volatility

    Each expiry is evaluated across the same moneyness grid so that
    the individual fitted smiles can be combined into one surface.
    """

    if not surface.smiles:
        raise ValueError("The volatility surface contains no smiles.")

    if surface.spot <= 0:
        raise ValueError("Spot price must be positive.")

    if minimum_moneyness <= 0:
        raise ValueError("Minimum moneyness must be positive.")

    if maximum_moneyness <= minimum_moneyness:
        raise ValueError(
            "Maximum moneyness must be greater than minimum moneyness."
        )

    if number_of_strikes < 2:
        raise ValueError("At least two strike points are required.")

    valuation_date = date.today()

    moneyness_values = np.linspace(
        minimum_moneyness,
        maximum_moneyness,
        number_of_strikes,
    )

    strikes = moneyness_values * surface.spot

    days_to_expiry = np.array(
        [
            max((smile.expiry - valuation_date).days, 0)
            for smile in surface.smiles
        ],
        dtype=float,
    )

    implied_volatilities = np.array(
        [
            [
                smile.implied_volatility(float(strike))
                for strike in strikes
            ]
            for smile in surface.smiles
        ],
        dtype=float,
    )

    moneyness_grid, expiry_grid = np.meshgrid(
        moneyness_values,
        days_to_expiry,
    )

    figure = plt.figure(figsize=(11, 7))

    axis = figure.add_subplot(
        111,
        projection="3d",
    )

    axis.plot_surface(
        moneyness_grid,
        expiry_grid,
        implied_volatilities,
        alpha=0.8,
    )

    for smile_index, smile in enumerate(surface.smiles):
        axis.plot(
            moneyness_values,
            np.full_like(
                moneyness_values,
                days_to_expiry[smile_index],
            ),
            implied_volatilities[smile_index],
            linewidth=1,
        )

    axis.set_title(
        f"{surface.symbol} Implied Volatility Surface"
    )

    axis.set_xlabel("Moneyness — Strike / Spot")
    axis.set_ylabel("Days to Expiry")
    axis.set_zlabel("Implied Volatility")

    figure.tight_layout()

    plt.show(block=True)

    return figure