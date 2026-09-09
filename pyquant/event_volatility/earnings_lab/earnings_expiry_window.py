from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)


class ExpiryProvider(Protocol):
    """
    Any market-data provider that can return available
    option expiries for a symbol.
    """

    def get_expiries(
        self,
        symbol: str,
    ) -> list[date]: ...


@dataclass(frozen=True)
class EarningsExpiryWindow:
    """
    Represents the option expiries surrounding an earnings event.

    short_expiry:
        The nearest expiry that does NOT contain the earnings event.

    long_expiry:
        The nearest expiry that DOES contain the earnings event.

    This distinction is important because the difference in implied
    variance between the two expiries can later be used to estimate
    the variance attributable specifically to earnings.
    """

    short_expiry: date
    long_expiry: date

    def __post_init__(self) -> None:
        if self.short_expiry >= self.long_expiry:
            raise ValueError("Short expiry must be before long expiry.")

    @classmethod
    def from_provider(
        cls,
        provider: ExpiryProvider,
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
    ) -> "EarningsExpiryWindow":
        """
        Construct the expiry window surrounding an earnings event.

        For after-market-close earnings:
            An option expiring on the earnings date expires before
            the announcement, so it belongs on the short side.

        For before-market-open earnings:
            An option expiring on the earnings date experiences
            the earnings announcement, so it belongs on the long side.

        During-market-hours and unknown releases are excluded for now
        because their treatment requires more precise timing data.
        """

        normalised_symbol = symbol.strip().upper()
        if not normalised_symbol:
            raise ValueError("Symbol cannot be empty.")

        return cls.from_expiries(
            expiries=provider.get_expiries(normalised_symbol),
            symbol=normalised_symbol,
            earnings_date=earnings_date,
            release_timing=release_timing,
        )

    @classmethod
    def from_expiries(
        cls,
        expiries: Iterable[date],
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
    ) -> "EarningsExpiryWindow":
        """Construct an earnings window from known contract expiries."""
        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        if release_timing == EarningsReleaseTiming.UNKNOWN:
            raise ValueError(
                "Cannot construct an earnings expiry window when "
                "release timing is unknown."
            )

        if release_timing == EarningsReleaseTiming.DURING_MARKET_HOURS:
            raise ValueError(
                "During-market-hours earnings require a precise "
                "announcement timestamp and are excluded for now."
            )

        expiries = sorted(set(expiries))

        if not expiries:
            raise ValueError(f"No option expiries found for {symbol}.")

        if release_timing == EarningsReleaseTiming.AFTER_MARKET_CLOSE:
            short_candidates = [
                expiry for expiry in expiries if expiry <= earnings_date
            ]

            long_candidates = [expiry for expiry in expiries if expiry > earnings_date]

        elif release_timing == EarningsReleaseTiming.BEFORE_MARKET_OPEN:
            short_candidates = [expiry for expiry in expiries if expiry < earnings_date]

            long_candidates = [expiry for expiry in expiries if expiry >= earnings_date]

        else:
            raise ValueError(f"Unsupported earnings release timing: {release_timing}")

        if not short_candidates:
            raise ValueError(
                f"No option expiry found before the earnings event "
                f"for {symbol} on {earnings_date}."
            )

        if not long_candidates:
            raise ValueError(
                f"No option expiry found containing the earnings event "
                f"for {symbol} on {earnings_date}."
            )

        return cls(
            short_expiry=max(short_candidates),
            long_expiry=min(long_candidates),
        )
