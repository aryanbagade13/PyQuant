import csv
from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.historical_dataset import (
    HistoricalEarningsDataset,
    HistoricalEarningsRecord,
)
from pyquant.event_volatility.earnings_lab.models.earnings_price_window import (
    EarningsPriceWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.models.earnings_report import (
    EarningsReport,
)


def make_report() -> EarningsReport:
    return EarningsReport(
        symbol=" aapl ",
        reported_date=date(2025, 1, 30),
        fiscal_period_end=date(2024, 12, 31),
        estimated_eps=2.35,
        actual_eps=2.40,
        estimated_revenue=124_000,
        actual_revenue=126_480,
    )


def make_window() -> EarningsPriceWindow:
    return EarningsPriceWindow(
        pre_event_date=date(2025, 1, 30),
        post_event_date=date(2025, 1, 31),
        pre_event_price=200,
        post_event_price=210,
    )


def test_record_calculates_analysis_fields() -> None:
    record = HistoricalEarningsRecord.from_report(
        make_report(),
        make_window(),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        implied_earnings_move=0.04,
    )

    assert record.symbol == "AAPL"
    assert record.eps_surprise == pytest.approx(0.05 / 2.35)
    assert record.revenue_surprise == pytest.approx(0.02)
    assert record.realised_earnings_return == pytest.approx(0.05)
    assert record.realised_earnings_move == pytest.approx(0.05)


def test_dataset_requires_a_price_window() -> None:
    with pytest.raises(ValueError, match="Missing price window"):
        HistoricalEarningsDataset.build([make_report()], {})


def test_dataset_rejects_duplicate_events() -> None:
    record = HistoricalEarningsRecord.from_report(make_report(), make_window())
    with pytest.raises(ValueError, match="duplicate"):
        HistoricalEarningsDataset((record, record))


def test_dataset_exports_stable_csv(tmp_path) -> None:
    report = make_report()
    dataset = HistoricalEarningsDataset.build(
        [report],
        {report.reported_date: make_window()},
    )

    path = dataset.to_csv(tmp_path / "earnings.csv")
    with path.open(newline="", encoding="utf-8") as input_file:
        rows = list(csv.DictReader(input_file))

    assert len(rows) == 1
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["release_timing"] == "unknown"
    assert rows[0]["realised_earnings_move"] == "0.050000000000000044"


def test_dataset_builds_directly_from_providers() -> None:
    report = make_report()

    class EarningsProvider:
        def get_historical_earnings(self, symbol):
            assert symbol == "AAPL"
            return [report]

    class PriceProvider:
        def get_historical_closes(self, symbol, start_date, end_date):
            return {
                date(2025, 1, 30): 200,
                date(2025, 1, 31): 210,
            }

    dataset = HistoricalEarningsDataset.from_providers(
        symbol="AAPL",
        earnings_provider=EarningsProvider(),
        price_provider=PriceProvider(),
        release_timings={
            report.reported_date: EarningsReleaseTiming.AFTER_MARKET_CLOSE
        },
        implied_moves={report.reported_date: 0.04},
    )

    assert len(dataset.records) == 1
    assert dataset.records[0].realised_earnings_move == pytest.approx(0.05)
    assert dataset.records[0].implied_earnings_move == 0.04


def test_provider_build_requires_release_timing() -> None:
    class EarningsProvider:
        def get_historical_earnings(self, symbol):
            return [make_report()]

    with pytest.raises(ValueError, match="Missing release timing"):
        HistoricalEarningsDataset.from_providers(
            symbol="AAPL",
            earnings_provider=EarningsProvider(),
            price_provider=object(),
            release_timings={},
        )


def test_dataset_retrieves_release_timing_automatically() -> None:
    report = make_report()

    class EarningsProvider:
        def get_historical_earnings(self, symbol):
            return [report]

    class PriceProvider:
        def get_historical_closes(self, symbol, start_date, end_date):
            return {
                date(2025, 1, 30): 200,
                date(2025, 1, 31): 210,
            }

    class TimingProvider:
        def get_release_timing(self, symbol, earnings_date):
            return EarningsReleaseTiming.AFTER_MARKET_CLOSE

    dataset = HistoricalEarningsDataset.from_providers(
        symbol="AAPL",
        earnings_provider=EarningsProvider(),
        price_provider=PriceProvider(),
        release_timing_provider=TimingProvider(),
    )

    assert dataset.records[0].release_timing == (
        EarningsReleaseTiming.AFTER_MARKET_CLOSE
    )


def test_dataset_rejects_unknown_automatic_timing() -> None:
    class EarningsProvider:
        def get_historical_earnings(self, symbol):
            return [make_report()]

    class TimingProvider:
        def get_release_timing(self, symbol, earnings_date):
            return EarningsReleaseTiming.UNKNOWN

    with pytest.raises(ValueError, match="Release timing is unknown"):
        HistoricalEarningsDataset.from_providers(
            symbol="AAPL",
            earnings_provider=EarningsProvider(),
            price_provider=object(),
            release_timing_provider=TimingProvider(),
        )
