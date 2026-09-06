from pyquant.data.market_snapshot import MarketSnapshot
from pyquant.event_volatility.earnings_lab.models.implied_move import ImpliedMove


def implied_move_from_snapshot(
    snapshot: MarketSnapshot,
) -> ImpliedMove:
    """
    Build an ImpliedMove from a MarketSnapshot.

    The function:
    1. Finds the strike closest to spot.
    2. Finds the call and put at that strike.
    3. Uses their mid prices to construct an ATM straddle.
    4. Returns an ImpliedMove object.
    """

    spot = snapshot.spot

    strikes = {
        quote.option.strike
        for quote in snapshot.option_quotes
    }

    if not strikes:
        raise ValueError(
            "Snapshot contains no option strikes."
        )

    atm_strike = min(
        strikes,
        key=lambda strike: abs(strike - spot),
    )

    call_quote = None
    put_quote = None

    for quote in snapshot.option_quotes:
        if quote.option.strike != atm_strike:
            continue

        if quote.option.option_type == "call":
            call_quote = quote

        elif quote.option.option_type == "put":
            put_quote = quote

    if call_quote is None:
        raise ValueError(
            f"No call found at ATM strike {atm_strike}."
        )

    if put_quote is None:
        raise ValueError(
            f"No put found at ATM strike {atm_strike}."
        )

    call_mid = call_quote.mid_price
    put_mid = put_quote.mid_price

    if call_mid is None:
        raise ValueError(
            f"No usable call midpoint at strike {atm_strike}."
        )

    if put_mid is None:
        raise ValueError(
            f"No usable put midpoint at strike {atm_strike}."
        )

    return ImpliedMove(
        spot=spot,
        atm_strike=atm_strike,
        call_mid=call_mid,
        put_mid=put_mid,
    )