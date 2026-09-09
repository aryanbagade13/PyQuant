from enum import Enum


class EarningsReleaseTiming(str, Enum):
    BEFORE_MARKET_OPEN = "before_market_open"
    AFTER_MARKET_CLOSE = "after_market_close"
    DURING_MARKET_HOURS = "during_market_hours"
    UNKNOWN = "unknown"
