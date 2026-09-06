import csv
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping

from pyquant.event_volatility.earnings_lab.models.earnings_price_window import (
    EarningsPriceWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.models.earnings_report import (
    EarningsReport,
)
from pyquant.event_volatility.earnings_lab.price_window_builder import (
    build_earnings_price_window,
)
from pyquant.event_volatility.earnings_lab.providers.earnings_provider import (
    EarningsProvider,
)
from pyquant.event_volatility.earnings_lab.providers.historical_price_provider import (
    HistoricalPriceProvider,
)
from pyquant.event_volatility.earnings_lab.providers.release_timing_provider import (
    ReleaseTimingProvider,
)


@dataclass(frozen=True)
class HistoricalEarningsRecord:
    """One analysis-ready observation for a historical earnings event."""

    symbol: str
    earnings_date: date
    release_timing: EarningsReleaseTiming
    fiscal_period_end: date
    estimated_eps: float | None
    actual_eps: float | None
    eps_surprise: float | None
    estimated_revenue: float | None
    actual_revenue: float | None
    revenue_surprise: float | None
    pre_earnings_date: date
    post_earnings_date: date
    pre_earnings_price: float
    post_earnings_price: float
    realised_earnings_return: float
    realised_earnings_move: float
    implied_earnings_move: float | None = None
    implied_move_atm_strike: float | None = None
    implied_move_option_expiry: date | None = None
    implied_move_call_symbol: str | None = None
    implied_move_put_symbol: str | None = None
    implied_move_call_price: float | None = None
    implied_move_put_price: float | None = None
    implied_move_call_timestamp: str | None = None
    implied_move_put_timestamp: str | None = None
    implied_move_spot_price: float | None = None
    implied_move_source: str | None = None
    market_cap: float | None = None
    sector: str | None = None

    def __post_init__(self) -> None:
        if self.implied_earnings_move is not None and self.implied_earnings_move < 0:
            raise ValueError("Implied earnings move cannot be negative.")
        if self.market_cap is not None and self.market_cap < 0:
            raise ValueError("Market cap cannot be negative.")

    @classmethod
    def from_report(
        cls,
        report: EarningsReport,
        price_window: EarningsPriceWindow,
        release_timing: EarningsReleaseTiming = EarningsReleaseTiming.UNKNOWN,
        implied_earnings_move: float | None = None,
        implied_move_atm_strike: float | None = None,
        implied_move_option_expiry: date | None = None,
        implied_move_call_symbol: str | None = None,
        implied_move_put_symbol: str | None = None,
        implied_move_call_price: float | None = None,
        implied_move_put_price: float | None = None,
        implied_move_call_timestamp: str | None = None,
        implied_move_put_timestamp: str | None = None,
        implied_move_spot_price: float | None = None,
        implied_move_source: str | None = None,
        market_cap: float | None = None,
        sector: str | None = None,
    ) -> "HistoricalEarningsRecord":
        return cls(
            symbol=report.symbol,
            earnings_date=report.reported_date,
            release_timing=release_timing,
            fiscal_period_end=report.fiscal_period_end,
            estimated_eps=report.estimated_eps,
            actual_eps=report.actual_eps,
            eps_surprise=report.calculated_eps_surprise,
            estimated_revenue=report.estimated_revenue,
            actual_revenue=report.actual_revenue,
            revenue_surprise=_relative_surprise(
                report.estimated_revenue, report.actual_revenue
            ),
            pre_earnings_date=price_window.pre_event_date,
            post_earnings_date=price_window.post_event_date,
            pre_earnings_price=price_window.pre_event_price,
            post_earnings_price=price_window.post_event_price,
            realised_earnings_return=price_window.event_return,
            realised_earnings_move=price_window.absolute_event_move,
            implied_earnings_move=implied_earnings_move,
            implied_move_atm_strike=implied_move_atm_strike,
            implied_move_option_expiry=implied_move_option_expiry,
            implied_move_call_symbol=implied_move_call_symbol,
            implied_move_put_symbol=implied_move_put_symbol,
            implied_move_call_price=implied_move_call_price,
            implied_move_put_price=implied_move_put_price,
            implied_move_call_timestamp=implied_move_call_timestamp,
            implied_move_put_timestamp=implied_move_put_timestamp,
            implied_move_spot_price=implied_move_spot_price,
            implied_move_source=implied_move_source,
            market_cap=market_cap,
            sector=sector.strip() if sector else None,
        )


@dataclass(frozen=True)
class HistoricalEarningsDataset:
    records: tuple[HistoricalEarningsRecord, ...]

    def __post_init__(self) -> None:
        keys = [(record.symbol, record.earnings_date) for record in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError("Dataset contains duplicate symbol and earnings-date rows.")

    @classmethod
    def build(
        cls,
        reports: Iterable[EarningsReport],
        price_windows: Mapping[date, EarningsPriceWindow],
        release_timings: Mapping[date, EarningsReleaseTiming] | None = None,
        implied_moves: Mapping[date, float] | None = None,
    ) -> "HistoricalEarningsDataset":
        release_timings = release_timings or {}
        implied_moves = implied_moves or {}
        records: list[HistoricalEarningsRecord] = []

        for report in reports:
            try:
                price_window = price_windows[report.reported_date]
            except KeyError as error:
                raise ValueError(
                    f"Missing price window for {report.symbol} "
                    f"on {report.reported_date}."
                ) from error

            records.append(
                HistoricalEarningsRecord.from_report(
                    report=report,
                    price_window=price_window,
                    release_timing=release_timings.get(
                        report.reported_date, EarningsReleaseTiming.UNKNOWN
                    ),
                    implied_earnings_move=implied_moves.get(report.reported_date),
                )
            )

        records.sort(key=lambda record: (record.symbol, record.earnings_date))
        return cls(tuple(records))

    @classmethod
    def from_providers(
        cls,
        symbol: str,
        earnings_provider: EarningsProvider,
        price_provider: HistoricalPriceProvider,
        release_timings: Mapping[date, EarningsReleaseTiming] | None = None,
        release_timing_provider: ReleaseTimingProvider | None = None,
        implied_moves: Mapping[date, float] | None = None,
    ) -> "HistoricalEarningsDataset":
        """Retrieve reports and construct event windows automatically."""
        reports = earnings_provider.get_historical_earnings(symbol)
        resolved_timings = dict(release_timings or {})
        price_windows: dict[date, EarningsPriceWindow] = {}

        for report in reports:
            timing = resolved_timings.get(report.reported_date)
            if timing is None and release_timing_provider is not None:
                timing = release_timing_provider.get_release_timing(
                    report.symbol,
                    report.reported_date,
                )
                resolved_timings[report.reported_date] = timing

            if timing is None:
                raise ValueError(
                    f"Missing release timing for {report.symbol} "
                    f"on {report.reported_date}."
                )
            if timing == EarningsReleaseTiming.UNKNOWN:
                raise ValueError(
                    f"Release timing is unknown for {report.symbol} "
                    f"on {report.reported_date}."
                )

            price_windows[report.reported_date] = build_earnings_price_window(
                provider=price_provider,
                symbol=report.symbol,
                earnings_date=report.reported_date,
                release_timing=timing,
            )

        return cls.build(
            reports=reports,
            price_windows=price_windows,
            release_timings=resolved_timings,
            implied_moves=implied_moves,
        )

    def to_csv(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(HistoricalEarningsRecord.__dataclass_fields__)

        with output_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                row = asdict(record)
                row["earnings_date"] = record.earnings_date.isoformat()
                row["fiscal_period_end"] = record.fiscal_period_end.isoformat()
                row["pre_earnings_date"] = record.pre_earnings_date.isoformat()
                row["post_earnings_date"] = record.post_earnings_date.isoformat()
                row["release_timing"] = record.release_timing.value
                if record.implied_move_option_expiry is not None:
                    row["implied_move_option_expiry"] = (
                        record.implied_move_option_expiry.isoformat()
                    )
                writer.writerow(row)

        return output_path


def _relative_surprise(
    estimate: float | None,
    actual: float | None,
) -> float | None:
    if estimate is None or actual is None or estimate == 0:
        return None
    return (actual - estimate) / abs(estimate)
