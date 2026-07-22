from datetime import date, timedelta

from pyquant.analysis.volatility_smile import build_volatility_smile
from pyquant.visualisation.iv_smile import plot_iv_smile
from pyquant.analysis.option_chain_analysis import analyse_option_chain
from pyquant.data.yahoo_finance_provider import YahooFinanceProvider
from pyquant.market.market_state import MarketState


provider = YahooFinanceProvider()

symbol = "AAPL"

expiries = provider.get_expiries(symbol)

if not expiries:
    raise ValueError(
        f"No option expiries returned for {symbol}."
    )

minimum_expiry = date.today() + timedelta(days=7)

valid_expiries = [
    expiry
    for expiry in expiries
    if expiry >= minimum_expiry
]

if not valid_expiries:
    raise ValueError(
        f"No expiries at least seven days away were returned for {symbol}."
    )

selected_expiry = valid_expiries[0]

snapshot = provider.get_snapshot(
    symbol=symbol,
    expiry=selected_expiry,
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
    expiry=selected_expiry,
    quotes=snapshot.option_quotes,
    market=market,
)

smile = build_volatility_smile(
    analysis=analysis,
    degree=2,
)

print("Option chain analysis")
print(f"Symbol: {analysis.symbol}")
print(f"Spot: {analysis.spot:.2f}")
print(f"Expiry: {analysis.expiry}")
print(f"Downloaded quotes: {len(snapshot.option_quotes)}")
print(f"Successfully analysed: {len(analysis.rows)}")
print(f"Calls analysed: {len(analysis.calls())}")
print(f"Puts analysed: {len(analysis.puts())}")

if analysis.rows:
    print(f"Average IV: {analysis.average_iv():.2%}")

    atm = analysis.at_the_money()

    print("\nAt-the-money option")
    print(f"Type: {atm.option_type}")
    print(f"Strike: {atm.strike:.2f}")
    print(f"Mid: {atm.mid_price:.2f}")
    print(f"IV: {atm.implied_volatility:.2%}")
    print(f"Delta: {atm.delta:.4f}")
    print(f"Gamma: {atm.gamma:.6f}")

print(
    f"\n{'Type':<8}"
    f"{'Strike':>9}"
    f"{'Mid':>9}"
    f"{'Spread':>9}"
    f"{'Money':>9}"
    f"{'IV':>9}"
    f"{'Delta':>10}"
    f"{'Gamma':>11}"
    f"{'Vega':>10}"
    f"{'Theta':>10}"
    f"{'Rho':>10}"
)

print("-" * 104)

for row in analysis.rows:
    print(
        f"{row.option_type:<8}"
        f"{row.strike:>9.2f}"
        f"{row.mid_price:>9.2f}"
        f"{row.spread:>9.2f}"
        f"{row.moneyness:>9.4f}"
        f"{row.implied_volatility:>8.2%}"
        f"{row.delta:>10.4f}"
        f"{row.gamma:>11.6f}"
        f"{row.vega:>10.4f}"
        f"{row.theta:>10.4f}"
        f"{row.rho:>10.4f}"
    )

smile = build_volatility_smile(
    analysis=analysis,
    degree=2,
)

plot_iv_smile(
    analysis=analysis,
    smile=smile
)