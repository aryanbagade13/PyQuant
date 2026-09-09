from datetime import date, timedelta

from pyquant.analysis.option_chain_analysis import analyse_option_chain
from pyquant.analysis.volatility_surface import build_volatility_surface
from pyquant.data.alpaca_provider import AlpacaProvider
from pyquant.market.market_state import MarketState
from pyquant.visualisation.volatility_surface_3d import (
    plot_volatility_surface,
)


def main() -> None:
    provider = AlpacaProvider()
    symbol = "AAPL"
    expiries = provider.get_expiries(symbol)

    if not expiries:
        raise ValueError(f"No option expiries returned for {symbol}.")

    minimum_expiry = date.today() + timedelta(days=7)

    valid_expiries = [expiry for expiry in expiries if expiry >= minimum_expiry]

    if not valid_expiries:
        raise ValueError(
            f"No expiries at least seven days away were returned for {symbol}."
        )

    # Use the first six suitable expiries.
    selected_expiries = valid_expiries[:6]

    analyses = []

    for expiry in selected_expiries:
        print(f"Downloading {symbol} option chain for {expiry}...")

        try:
            snapshot = provider.get_snapshot(
                symbol=symbol,
                expiry=expiry,
            )

            market = MarketState(
                spot=snapshot.spot,
                volatility=0.20,
                risk_free_rate=0.04,
                dividend_yield=0.0,
                valuation_date=date.today(),
            )

            analysis = analyse_option_chain(
                symbol=snapshot.symbol,
                expiry=expiry,
                quotes=snapshot.option_quotes,
                market=market,
            )

            if not analysis.rows:
                print(f"Skipping {expiry}: no options were successfully analysed.")
                continue

            analyses.append(analysis)

            print(f"Analysed {len(analysis.rows)} options for expiry {expiry}.")

        except Exception as error:
            print(f"Skipping {expiry} because analysis failed: {error}")

    if len(analyses) < 2:
        raise ValueError(
            "At least two successful expiry analyses are required "
            "to build a useful volatility surface."
        )

    surface = build_volatility_surface(
        analyses=analyses,
        degree=2,
    )

    print("\nVolatility surface built")
    print(f"Symbol: {surface.symbol}")
    print(f"Spot: {surface.spot:.2f}")
    print(f"Number of smiles: {len(surface.smiles)}")

    print("\nExpiries included:")

    for smile in surface.smiles:
        print(f"{smile.expiry}: {len(smile.strikes)} IV observations")

    plot_volatility_surface(
        surface=surface,
        minimum_moneyness=0.90,
        maximum_moneyness=1.10,
        number_of_strikes=100,
    )


if __name__ == "__main__":
    main()
