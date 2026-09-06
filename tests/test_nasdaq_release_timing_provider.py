from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.providers.nasdaq_release_timing_provider import (
    NasdaqReleaseTimingProvider,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("time-pre-market", EarningsReleaseTiming.BEFORE_MARKET_OPEN),
        ("Pre-Market", EarningsReleaseTiming.BEFORE_MARKET_OPEN),
        ("BMO", EarningsReleaseTiming.BEFORE_MARKET_OPEN),
        ("time-after-hours", EarningsReleaseTiming.AFTER_MARKET_CLOSE),
        ("After Hours", EarningsReleaseTiming.AFTER_MARKET_CLOSE),
        ("AMC", EarningsReleaseTiming.AFTER_MARKET_CLOSE),
        ("time-not-supplied", EarningsReleaseTiming.UNKNOWN),
        (None, EarningsReleaseTiming.UNKNOWN),
    ],
)
def test_normalises_nasdaq_timing_labels(raw_value, expected) -> None:
    assert NasdaqReleaseTimingProvider._normalise_timing(raw_value) == expected


def test_finds_symbol_case_insensitively_and_caches_date(monkeypatch) -> None:
    provider = NasdaqReleaseTimingProvider()
    calls = []

    def request(earnings_date):
        calls.append(earnings_date)
        return {
            "data": {
                "rows": [
                    {"symbol": "MSFT", "time": "time-pre-market"},
                    {"symbol": "AAPL", "time": "time-after-hours"},
                ]
            }
        }

    monkeypatch.setattr(provider, "_request_json", request)
    event_date = date(2025, 1, 30)

    assert provider.get_release_timing(" aapl ", event_date) == (
        EarningsReleaseTiming.AFTER_MARKET_CLOSE
    )
    assert provider.get_release_timing("MSFT", event_date) == (
        EarningsReleaseTiming.BEFORE_MARKET_OPEN
    )
    assert calls == [event_date]


def test_missing_symbol_returns_unknown(monkeypatch) -> None:
    provider = NasdaqReleaseTimingProvider()
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda earnings_date: {"data": {"rows": []}},
    )

    assert provider.get_release_timing("AAPL", date(2025, 1, 30)) == (
        EarningsReleaseTiming.UNKNOWN
    )


def test_rejects_malformed_rows() -> None:
    with pytest.raises(RuntimeError, match="invalid earnings calendar rows"):
        NasdaqReleaseTimingProvider._extract_rows({"data": {"rows": {}}})
