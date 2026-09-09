from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.providers.alpaca_historical_implied_move_provider import (
    AlpacaHistoricalImpliedMoveProvider,
    HistoricalOptionBar,
)


def make_provider() -> AlpacaHistoricalImpliedMoveProvider:
    return AlpacaHistoricalImpliedMoveProvider("key", "secret")


def test_selects_nearest_complete_call_put_pair() -> None:
    contracts = [
        {"symbol": "C230", "strike_price": "230", "type": "call"},
        {"symbol": "P230", "strike_price": "230", "type": "put"},
        {"symbol": "C235", "strike_price": "235", "type": "call"},
        {"symbol": "P235", "strike_price": "235", "type": "put"},
        {"symbol": "C240", "strike_price": "240", "type": "call"},
    ]

    call, put, strike = make_provider()._select_atm_pair(contracts, 236)

    assert strike == 235
    assert call["symbol"] == "C235"
    assert put["symbol"] == "P235"


def test_after_close_chooses_first_expiry_after_event(monkeypatch) -> None:
    provider = make_provider()
    payload = {
        "option_contracts": [
            {
                "symbol": "C1",
                "expiration_date": "2025-01-31",
                "strike_price": "235",
                "type": "call",
            },
            {
                "symbol": "P1",
                "expiration_date": "2025-01-31",
                "strike_price": "235",
                "type": "put",
            },
            {
                "symbol": "C2",
                "expiration_date": "2025-02-07",
                "strike_price": "235",
                "type": "call",
            },
        ]
    }
    captured = {}

    def get_json(url, params):
        captured.update(params)
        return payload

    monkeypatch.setattr(provider, "_get_json", get_json)
    contracts = provider._get_candidate_contracts(
        "AAPL",
        date(2025, 1, 30),
        EarningsReleaseTiming.AFTER_MARKET_CLOSE,
    )

    assert {contract["symbol"] for contract in contracts} == {"C1", "P1"}
    assert captured["status"] == "inactive"
    assert captured["expiration_date_gte"] == "2025-01-31"


def test_builds_implied_move_from_pre_cutoff_bars(monkeypatch) -> None:
    provider = make_provider()
    contracts = [
        {
            "symbol": "AAPL_CALL",
            "strike_price": "235",
            "type": "call",
            "expiration_date": "2025-01-31",
        },
        {
            "symbol": "AAPL_PUT",
            "strike_price": "235",
            "type": "put",
            "expiration_date": "2025-01-31",
        },
    ]
    monkeypatch.setattr(
        provider,
        "_get_candidate_contracts",
        lambda symbol, earnings_date, timing: contracts,
    )
    monkeypatch.setattr(
        provider,
        "_get_pre_cutoff_bars",
        lambda symbols, cutoff: {
            "AAPL_CALL": HistoricalOptionBar(
                4.25, datetime(2025, 1, 30, 20, 54, tzinfo=timezone.utc)
            ),
            "AAPL_PUT": HistoricalOptionBar(
                3.75, datetime(2025, 1, 30, 20, 53, tzinfo=timezone.utc)
            ),
        },
    )

    result = provider.get_implied_move(
        "AAPL",
        date(2025, 1, 30),
        EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        200,
    )

    assert result.atm_strike == 235
    assert result.straddle_price == 8
    assert result.implied_move_pct == pytest.approx(0.04)
    assert result.expiry == date(2025, 1, 31)
    assert result.call_symbol == "AAPL_CALL"


def test_rejects_stale_historical_option_bar(monkeypatch) -> None:
    provider = AlpacaHistoricalImpliedMoveProvider(
        "key", "secret", max_staleness_minutes=30
    )
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda url, params: {
            "bars": {
                "CALL": [{"c": 5, "t": "2025-01-30T18:00:00Z"}],
            }
        },
    )

    with pytest.raises(ValueError, match="stale"):
        provider._get_pre_cutoff_bars(
            ["CALL"],
            datetime(2025, 1, 30, 15, 55, tzinfo=ZoneInfo("America/New_York")),
        )
