from datetime import date

import pytest

from pyquant.event_volatility.earnings_lab.providers.alpha_vantage_earnings_provider import (
    AlphaVantageEarningsProvider,
)


def test_provider_parses_and_orders_quarterly_reports(monkeypatch) -> None:
    provider = AlphaVantageEarningsProvider(api_key="test")
    payload = {
        "quarterlyEarnings": [
            {
                "fiscalDateEnding": "2024-12-31",
                "reportedDate": "2025-01-30",
                "reportedEPS": "2.40",
                "estimatedEPS": "2.35",
                "surprise": "0.05",
                "surprisePercentage": "2.1277",
            },
            {
                "fiscalDateEnding": "2024-09-30",
                "reportedDate": "2024-10-31",
                "reportedEPS": "None",
                "estimatedEPS": "1.50",
                "surprise": "None",
                "surprisePercentage": "None",
            },
        ]
    }
    monkeypatch.setattr(provider, "_request_json", lambda symbol: payload)

    reports = provider.get_historical_earnings(" aapl ")

    assert [report.reported_date for report in reports] == [
        date(2024, 10, 31),
        date(2025, 1, 30),
    ]
    assert reports[0].actual_eps is None
    assert reports[1].symbol == "AAPL"
    assert reports[1].actual_eps == 2.40


def test_provider_surfaces_api_messages(monkeypatch) -> None:
    provider = AlphaVantageEarningsProvider(api_key="test")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda symbol: {"Note": "Rate limit reached"},
    )

    with pytest.raises(RuntimeError, match="Rate limit reached"):
        provider.get_historical_earnings("AAPL")
