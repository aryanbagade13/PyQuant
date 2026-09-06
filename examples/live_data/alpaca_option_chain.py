from datetime import date, timedelta

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest

from pyquant.config import (
    ALPACA_API_KEY,
    ALPACA_SECRET_KEY,
)

client = OptionHistoricalDataClient(
    api_key=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
)

symbol = "AAPL"
expiry = date.today() + timedelta(days=30)

request = OptionChainRequest(
    underlying_symbol=symbol,
    expiration_date_gte=expiry,
    expiration_date_lte=expiry + timedelta(days=7),
)

chain = client.get_option_chain(request)

print(f"Contracts returned: {len(chain)}")

for contract_symbol, snapshot in list(chain.items())[:10]:
    quote = snapshot.latest_quote
    trade = snapshot.latest_trade

    bid = quote.bid_price if quote is not None else None
    ask = quote.ask_price if quote is not None else None
    last = trade.price if trade is not None else None

    quote_time = quote.timestamp if quote is not None else None
    trade_time = trade.timestamp if trade is not None else None

    print(
        f"{contract_symbol:<24} "
        f"Bid={bid!s:<10} "
        f"Ask={ask!s:<10} "
        f"Last={last!s:<10} "
        f"Quote time={quote_time} "
        f"Trade time={trade_time}"
    )
