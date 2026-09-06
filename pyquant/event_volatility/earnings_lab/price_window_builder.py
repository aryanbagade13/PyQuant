import math
from datetime import date, timedelta

from pyquant.event_volatility.earnings_lab.models.earnings_price_window import (
    EarningsPriceWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.providers.historical_price_provider import (
    HistoricalPriceProvider,
)


def build_earnings_price_window(
    provider: HistoricalPriceProvider,
    symbol: str,
    earnings_date: date,
    release_timing: EarningsReleaseTiming,
    search_days: int = 10,
) -> EarningsPriceWindow:
    """Select uncontaminated closes immediately around an earnings release.

    After-close releases use that session's close and the following session.
    Before-open releases use the preceding session and the release-day session.
    Trading dates come from the provider, so weekends and market holidays are
    handled without maintaining a separate exchange calendar.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if search_days < 1:
        raise ValueError("Search days must be positive.")
    if release_timing == EarningsReleaseTiming.UNKNOWN:
        raise ValueError("Release timing is required to build a price window.")
    if release_timing == EarningsReleaseTiming.DURING_MARKET_HOURS:
        raise ValueError(
            "During-market-hours earnings require an exact release timestamp."
        )

    prices = provider.get_historical_closes(
        symbol=symbol,
        start_date=earnings_date - timedelta(days=search_days),
        end_date=earnings_date + timedelta(days=search_days),
    )
    valid_prices: dict[date, float] = {}
    for trading_date, close in prices.items():
        if close is None:
            continue
        numeric_close = float(close)
        if math.isfinite(numeric_close) and numeric_close > 0:
            valid_prices[trading_date] = numeric_close

    if release_timing == EarningsReleaseTiming.AFTER_MARKET_CLOSE:
        pre_candidates = [day for day in valid_prices if day <= earnings_date]
        post_candidates = [day for day in valid_prices if day > earnings_date]
    else:
        pre_candidates = [day for day in valid_prices if day < earnings_date]
        post_candidates = [day for day in valid_prices if day >= earnings_date]

    if not pre_candidates or not post_candidates:
        raise ValueError(
            f"Insufficient historical prices around {symbol} earnings "
            f"on {earnings_date}."
        )

    pre_date = max(pre_candidates)
    post_date = min(post_candidates)
    return EarningsPriceWindow(
        pre_event_date=pre_date,
        post_event_date=post_date,
        pre_event_price=valid_prices[pre_date],
        post_event_price=valid_prices[post_date],
    )
