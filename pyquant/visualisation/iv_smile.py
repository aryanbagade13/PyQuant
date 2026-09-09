import matplotlib.pyplot as plt

from pyquant.analysis.option_chain_analysis import OptionChainAnalysis
from pyquant.analysis.volatility_smile import (
    VolatilitySmile,
    build_volatility_smile,
)


def plot_iv_smile(
    analysis: OptionChainAnalysis,
    smile: VolatilitySmile | None = None,
) -> None:
    if smile is None:
        smile = build_volatility_smile(analysis)

    fitted_strikes, fitted_ivs = smile.fitted_points()

    figure, axis = plt.subplots()

    axis.scatter(
        smile.strikes,
        [implied_volatility * 100 for implied_volatility in smile.observed_ivs],
        label="Observed IV",
        alpha=0.7,
    )

    axis.plot(
        fitted_strikes,
        fitted_ivs * 100,
        linewidth=2,
        label="Fitted smile",
    )

    axis.axvline(
        x=analysis.spot,
        linestyle="--",
        label=f"Spot: {analysis.spot:.2f}",
    )

    axis.set_title(
        f"{analysis.symbol} Implied Volatility Smile\nExpiry: {analysis.expiry}"
    )
    axis.set_xlabel("Strike")
    axis.set_ylabel("Implied volatility (%)")
    axis.legend()
    axis.grid(True)

    figure.tight_layout()
    plt.show()
