from datetime import date, timedelta

from pyquant.analysis.option_chain_analysis import analyse_option_chain
from pyquant.analysis.volatility_smile import build_volatility_smile
from pyquant.data.alpaca_provider import AlpacaProvider
from pyquant.data.yahoo_finance_provider import YahooFinanceProvider
from pyquant.market.market_state import MarketState
from pyquant.visualisation.iv_smile import plot_iv_smile

provider = YahooFinanceProvider()
alpaca_provider = AlpacaProvider()

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

selected_expiry = valid_expiries[0]

print(f"Downloading {symbol} option chain for {selected_expiry}...")

snapshot = alpaca_provider.get_snapshot(  # have replaced with Alpaca
    symbol=symbol,
    expiry=selected_expiry,
)

print(f"Spot: {snapshot.spot:.2f}")
print(f"Downloaded quotes: {len(snapshot.option_quotes)}")

positive_bid_and_ask = sum(
    1 for quote in snapshot.option_quotes if quote.bid > 0.0 and quote.ask > 0.0
)

last_price_fallbacks = sum(
    1
    for quote in snapshot.option_quotes
    if (
        not (quote.bid > 0.0 and quote.ask > 0.0)
        and quote.last_price is not None
        and quote.last_price > 0.0
    )
)

print(f"Quotes with positive bid and ask: {positive_bid_and_ask}")

print(f"Quotes using last-price fallback: {last_price_fallbacks}")

print("\nFirst ten downloaded quotes:")

for quote in snapshot.option_quotes[:10]:
    price_source = "midpoint" if quote.bid > 0.0 and quote.ask > 0.0 else "last price"

    spread_text = f"{quote.spread:.2f}" if quote.spread is not None else "N/A"

    last_trade = (
        quote.last_trade_time.strftime("%Y-%m-%d %H:%M:%S")
        if quote.last_trade_time is not None
        else "N/A"
    )

    print(
        f"{quote.option.option_type:<5} "
        f"Strike={quote.option.strike:<8.2f} "
        f"Bid={quote.bid:<8.2f} "
        f"Ask={quote.ask:<8.2f} "
        f"Last={quote.last_price or 0.0:<8.2f} "
        f"Last trade={last_trade:<19} "
        f"Price={quote.mid_price:<8.2f} "
        f"Spread={spread_text:<8} "
        f"Source={price_source}"
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

print("\nAnalysis results")
print(f"Rows analysed: {len(analysis.rows)}")
print(f"Calls: {len(analysis.calls())}")
print(f"Puts: {len(analysis.puts())}")

if not analysis.rows:
    raise ValueError("No options were successfully analysed.")

print("\nFirst analysed rows:")

for row in analysis.rows[:5]:
    spread_text = f"{row.spread:.4f}" if row.spread is not None else "N/A"

    print(
        f"{row.option_type:<5} "
        f"Strike={row.strike:<8.2f} "
        f"IV={row.implied_volatility:.2%} "
        f"Spread={spread_text:<8} "
        f"Moneyness={row.moneyness:.4f}"
    )


smile = build_volatility_smile(
    analysis=analysis,
    degree=2,
)

print("\nSmile successfully built!")

plot_iv_smile(
    analysis=analysis,
    smile=smile,
)
