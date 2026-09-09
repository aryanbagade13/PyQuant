"""Run one historical earnings-volatility estimate with live market data."""

from datetime import date

from pyquant.event_volatility.earnings_lab.models.earnings_move_comparison import (
    EarningsMoveComparison,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.price_window_builder import (
    build_earnings_price_window,
)
from pyquant.event_volatility.earnings_lab.providers import (
    AlpacaHistoricalEarningsVarianceProvider,
)

# Edit these inputs to investigate a different historical earnings event.
SYMBOL = "AAPL"
EARNINGS_DATE = date(2025, 1, 30)
RELEASE_TIMING = EarningsReleaseTiming.AFTER_MARKET_CLOSE
RISK_FREE_RATE = 0.0440
DIVIDEND_YIELD = 0.0


def main() -> None:
    provider = AlpacaHistoricalEarningsVarianceProvider()
    estimate = provider.get_earnings_variance(
        symbol=SYMBOL,
        earnings_date=EARNINGS_DATE,
        release_timing=RELEASE_TIMING,
        risk_free_rate=RISK_FREE_RATE,
        dividend_yield=DIVIDEND_YIELD,
    )
    price_window = build_earnings_price_window(
        provider=provider,
        symbol=SYMBOL,
        earnings_date=EARNINGS_DATE,
        release_timing=RELEASE_TIMING,
    )
    comparison = EarningsMoveComparison(
        implied_move=estimate.earnings_implied_move,
        price_window=price_window,
    )

    move = estimate.earnings_implied_move
    lower_price = estimate.spot * (1.0 - move)
    upper_price = estimate.spot * (1.0 + move)

    print(f"\nHistorical earnings-volatility estimate: {estimate.symbol}")
    print(f"Earnings date: {EARNINGS_DATE:%d %B %Y} ({RELEASE_TIMING.value})")
    print(f"Observation cutoff: {estimate.observation_time.isoformat()}")
    print(f"Stock price at cutoff: ${estimate.spot:.2f}")
    print()
    print(
        f"Short expiry: {estimate.short_expiry} | "
        f"ATM strike: ${estimate.short_atm_strike:.2f} | "
        f"average IV: {estimate.short_atm_iv:.2%}"
    )
    print(
        f"Long expiry:  {estimate.long_expiry} | "
        f"ATM strike: ${estimate.long_atm_strike:.2f} | "
        f"average IV: {estimate.long_atm_iv:.2%}"
    )
    print()
    print(f"Ordinary implied volatility: {estimate.ordinary_implied_volatility:.2%}")
    print(f"Earnings-only implied move: {move:.2%}")
    print(f"Implied price range: ${lower_price:.2f} to ${upper_price:.2f}")
    print(f"Data source: {estimate.source}")
    print()
    direction = "rose" if comparison.realised_return >= 0 else "fell"
    print("Realised earnings reaction")
    print(
        f"Closing-price window: {price_window.pre_event_date} "
        f"(${price_window.pre_event_price:.2f}) to "
        f"{price_window.post_event_date} "
        f"(${price_window.post_event_price:.2f})"
    )
    print(
        f"AAPL {direction} {comparison.realised_move:.2%}; "
        f"the market implied {comparison.implied_move:.2%}."
    )
    print(
        f"The options market {comparison.market_assessment} the move by "
        f"{abs(comparison.move_difference):.2%}."
    )
    if comparison.realised_to_implied_ratio is not None:
        print(f"Realised/implied ratio: {comparison.realised_to_implied_ratio:.2f}x")


if __name__ == "__main__":
    main()
