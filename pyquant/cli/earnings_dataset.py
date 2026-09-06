import argparse
from datetime import date
from pathlib import Path

from pyquant.data.yahoo_finance_provider import YahooFinanceProvider
from pyquant.event_volatility.earnings_lab.historical_dataset import (
    HistoricalEarningsDataset,
    HistoricalEarningsRecord,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.price_window_builder import (
    build_earnings_price_window,
)
from pyquant.event_volatility.earnings_lab.providers import (
    AlpacaHistoricalImpliedMoveProvider,
    AlphaVantageEarningsProvider,
    NasdaqReleaseTimingProvider,
)


def build_recent_dataset(
    symbol: str,
    max_events: int = 1,
    event_date: date | None = None,
    reviewed_timing: EarningsReleaseTiming | None = None,
    include_implied_move: bool = True,
) -> HistoricalEarningsDataset:
    """Build recent events, skipping rows whose release time is unavailable."""
    if max_events < 1:
        raise ValueError("Max events must be positive.")

    earnings_provider = AlphaVantageEarningsProvider()
    timing_provider = NasdaqReleaseTimingProvider()
    price_provider = YahooFinanceProvider()
    implied_move_provider = (
        AlpacaHistoricalImpliedMoveProvider() if include_implied_move else None
    )
    reports = earnings_provider.get_historical_earnings(symbol)
    if event_date is not None:
        reports = [report for report in reports if report.reported_date == event_date]
        if not reports:
            raise RuntimeError(
                f"No earnings report found for {symbol.upper()} on {event_date}."
            )
    records: list[HistoricalEarningsRecord] = []

    for report in reversed(reports):
        timing = reviewed_timing or timing_provider.get_release_timing(
            report.symbol, report.reported_date
        )
        if timing == EarningsReleaseTiming.UNKNOWN:
            continue

        price_window = build_earnings_price_window(
            provider=price_provider,
            symbol=report.symbol,
            earnings_date=report.reported_date,
            release_timing=timing,
        )
        implied_move = None
        implied_move_spot = None
        if implied_move_provider is not None:
            raw_closes = price_provider.get_historical_raw_closes(
                report.symbol,
                price_window.pre_event_date,
                price_window.pre_event_date,
            )
            try:
                implied_move_spot = raw_closes[price_window.pre_event_date]
            except KeyError as error:
                raise RuntimeError(
                    f"No raw pre-event close found for {report.symbol} "
                    f"on {price_window.pre_event_date}."
                ) from error
            implied_move = implied_move_provider.get_implied_move(
                symbol=report.symbol,
                earnings_date=report.reported_date,
                release_timing=timing,
                spot=implied_move_spot,
            )
        records.append(
            HistoricalEarningsRecord.from_report(
                report=report,
                price_window=price_window,
                release_timing=timing,
                implied_earnings_move=(
                    implied_move.implied_move_pct if implied_move else None
                ),
                implied_move_atm_strike=(
                    implied_move.atm_strike if implied_move else None
                ),
                implied_move_option_expiry=(
                    implied_move.expiry if implied_move else None
                ),
                implied_move_call_symbol=(
                    implied_move.call_symbol if implied_move else None
                ),
                implied_move_put_symbol=(
                    implied_move.put_symbol if implied_move else None
                ),
                implied_move_call_price=(
                    implied_move.call_mid if implied_move else None
                ),
                implied_move_put_price=(
                    implied_move.put_mid if implied_move else None
                ),
                implied_move_call_timestamp=(
                    implied_move.call_observation_time.isoformat()
                    if implied_move and implied_move.call_observation_time
                    else None
                ),
                implied_move_put_timestamp=(
                    implied_move.put_observation_time.isoformat()
                    if implied_move and implied_move.put_observation_time
                    else None
                ),
                implied_move_spot_price=implied_move_spot,
                implied_move_source=(
                    implied_move.source if implied_move else None
                ),
            )
        )
        if len(records) == max_events:
            break

    if not records:
        raise RuntimeError(
            f"No usable historical earnings events found for {symbol.upper()}."
        )
    return HistoricalEarningsDataset(tuple(reversed(records)))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a recent historical earnings research dataset."
    )
    parser.add_argument("symbol", help="Equity ticker, for example AAPL")
    parser.add_argument("--max-events", type=int, default=1)
    parser.add_argument("--event-date", type=date.fromisoformat)
    parser.add_argument(
        "--release-timing",
        choices=[
            EarningsReleaseTiming.BEFORE_MARKET_OPEN.value,
            EarningsReleaseTiming.AFTER_MARKET_CLOSE.value,
        ],
        help="Reviewed override; requires --event-date.",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--without-implied-move",
        action="store_true",
        help="Skip historical Alpaca option data.",
    )
    args = parser.parse_args()

    symbol = args.symbol.strip().upper()
    output = args.output or Path(
        f"data_cache/research/{symbol.lower()}_earnings.csv"
    )
    if args.release_timing and args.event_date is None:
        parser.error("--release-timing requires --event-date")
    reviewed_timing = (
        EarningsReleaseTiming(args.release_timing) if args.release_timing else None
    )
    dataset = build_recent_dataset(
        symbol,
        args.max_events,
        event_date=args.event_date,
        reviewed_timing=reviewed_timing,
        include_implied_move=not args.without_implied_move,
    )
    dataset.to_csv(output)
    print(f"Wrote {len(dataset.records)} event(s) to {output}")


if __name__ == "__main__":
    main()
