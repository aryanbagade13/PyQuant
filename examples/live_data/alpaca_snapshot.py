from datetime import date

from pyquant.data.alpaca_provider import AlpacaProvider


provider = AlpacaProvider()

snapshot = provider.get_snapshot(
    symbol="AAPL",
    expiry=date(2026, 10, 2),
)

print("Symbol:", snapshot.symbol)
print("Spot:", snapshot.spot)
print("Timestamp:", snapshot.timestamp)
print("Number of quotes:", len(snapshot.option_quotes))

print("\nFirst ten quotes:")

for quote in snapshot.option_quotes[:10]:
    print(
        f"{quote.option.option_type:<5} "
        f"Strike={quote.option.strike:<8.2f} "
        f"Bid={quote.bid:<8.2f} "
        f"Ask={quote.ask:<8.2f} "
        f"Last={quote.last_price} "
        f"Trade time={quote.last_trade_time}"
    )
