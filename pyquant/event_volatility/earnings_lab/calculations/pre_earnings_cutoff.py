from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)

NEW_YORK = ZoneInfo("America/New_York")


def get_pre_earnings_cutoff(
    earnings_date: date,
    release_timing: EarningsReleaseTiming,
) -> datetime:
    """
    Return the latest safe pre-earnings observation timestamp.

    Rules:
    - After-market-close earnings:
        use 15:55 New York time on the earnings date.

    - Before-market-open earnings:
        use 15:55 New York time on the previous weekday.

    - During-market-hours:
        excluded for now because we would need the precise
        earnings release timestamp.

    - Unknown timing:
        excluded to avoid look-ahead bias.
    """

    market_cutoff_time = time(
        hour=15,
        minute=55,
    )

    if release_timing == EarningsReleaseTiming.AFTER_MARKET_CLOSE:
        observation_date = earnings_date

    elif release_timing == EarningsReleaseTiming.BEFORE_MARKET_OPEN:
        observation_date = _previous_weekday(earnings_date)

    elif release_timing == EarningsReleaseTiming.DURING_MARKET_HOURS:
        raise ValueError(
            "During-market-hours earnings are excluded because "
            "the precise announcement time is required."
        )

    elif release_timing == EarningsReleaseTiming.UNKNOWN:
        raise ValueError(
            "Cannot determine a safe pre-earnings cutoff when "
            "release timing is unknown."
        )

    else:
        raise ValueError(f"Unsupported earnings release timing: {release_timing}")

    return datetime.combine(
        observation_date,
        market_cutoff_time,
        tzinfo=NEW_YORK,
    )


def _previous_weekday(
    current_date: date,
) -> date:
    """
    Return the previous Monday-Friday date.

    This handles weekends, but not US market holidays yet.
    """

    previous_date = current_date - timedelta(days=1)

    while previous_date.weekday() >= 5:
        previous_date -= timedelta(days=1)

    return previous_date
