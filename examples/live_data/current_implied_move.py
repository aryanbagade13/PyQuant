from datetime import date

from pyquant.data.alpaca_provider import AlpacaProvider
from pyquant.event_volatility.earnings_lab.calculations.implied_move_from_snapshot import (
    implied_move_from_snapshot,
)


provider = AlpacaProvider()

snapshot = provider.get_snapshot(
    symbol="AAPL",
    expiry=date(2026, 10, 2),
)

move = implied_move_from_snapshot(snapshot)

print("Spot:", move.spot)
print("ATM strike:", move.atm_strike)
print("Call mid:", move.call_mid)
print("Put mid:", move.put_mid)
print("Straddle price:", move.straddle_price)
print("Implied move:", move.implied_move_pct)
print(
    "Implied move %:",
    f"{move.implied_move_pct:.2%}",
)
