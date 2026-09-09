from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from pyquant.event_volatility.earnings_lab.calculations.pre_earnings_cutoff import (
    NEW_YORK,
)
from pyquant.event_volatility.earnings_lab.earnings_expiry_window import (
    EarningsExpiryWindow,
)

if TYPE_CHECKING:
    from pyquant.event_volatility.earnings_lab.providers.historical_price_provider import (
        HistoricalPriceProvider,
    )


def select_option_observation_cutoff(
    provider: HistoricalPriceProvider,
    symbol: str,
    earnings_date: date,
    expiry_window: EarningsExpiryWindow,
    trading_sessions_before_earnings: int = 10,
    search_days: int = 45,
) -> datetime:
    """Choose a reproducible cutoff while both option expiries still exist.

    The selected session is counted backwards using actual trading dates from
    the price provider. This handles weekends and market holidays without
    pretending that every weekday was an open session.

    A valid cutoff must be strictly before both the earnings date and the short
    expiry. If the requested research horizon is too late for the short expiry,
    an error is raised instead of silently changing the horizon.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if trading_sessions_before_earnings < 1:
        raise ValueError("Trading sessions before earnings must be positive.")
    if search_days < 1:
        raise ValueError("Search days must be positive.")

    prices = provider.get_historical_closes(
        symbol=symbol,
        start_date=earnings_date - timedelta(days=search_days),
        end_date=earnings_date - timedelta(days=1),
    )

    trading_dates: list[date] = []
    for trading_date, close in prices.items():
        if trading_date >= earnings_date or close is None:
            continue
        numeric_close = float(close)
        if math.isfinite(numeric_close) and numeric_close > 0:
            trading_dates.append(trading_date)

    trading_dates = sorted(set(trading_dates))
    if len(trading_dates) < trading_sessions_before_earnings:
        raise ValueError(
            f"Only {len(trading_dates)} valid trading sessions were found "
            f"before {symbol} earnings on {earnings_date}; "
            f"{trading_sessions_before_earnings} are required."
        )

    observation_date = trading_dates[-trading_sessions_before_earnings]
    if observation_date >= expiry_window.short_expiry:
        raise ValueError(
            f"The requested observation date {observation_date} is not before "
            f"the short expiry {expiry_window.short_expiry}. Increase "
            "trading_sessions_before_earnings."
        )

    return datetime.combine(
        observation_date,
        time(hour=15, minute=55),
        tzinfo=NEW_YORK,
    )
