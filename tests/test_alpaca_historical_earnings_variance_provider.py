from datetime import date, datetime, timedelta, timezone

import pytest

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.providers.alpaca_historical_earnings_variance_provider import (
    AlpacaHistoricalEarningsVarianceProvider,
)
from pyquant.event_volatility.earnings_lab.providers.alpaca_historical_implied_move_provider import (
    HistoricalOptionBar,
)
from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.pricing.black_scholes import black_scholes_price


class FakePriceProvider:
    def __init__(self, spot: float = 200.0) -> None:
        self.spot = spot
        self.sessions = [
            date(2025, 1, 2),
            date(2025, 1, 3),
            date(2025, 1, 6),
            date(2025, 1, 7),
            date(2025, 1, 8),
            date(2025, 1, 9),
            date(2025, 1, 10),
            date(2025, 1, 13),
            date(2025, 1, 14),
            date(2025, 1, 15),
            date(2025, 1, 16),
            date(2025, 1, 17),
            date(2025, 1, 21),
            date(2025, 1, 22),
            date(2025, 1, 23),
            date(2025, 1, 24),
            date(2025, 1, 27),
            date(2025, 1, 28),
            date(2025, 1, 29),
        ]

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        return {
            session: self.spot
            for session in self.sessions
            if start_date <= session <= end_date
        }


def make_provider() -> AlpacaHistoricalEarningsVarianceProvider:
    return AlpacaHistoricalEarningsVarianceProvider("key", "secret")


def make_contracts() -> list[dict[str, str]]:
    return [
        {
            "symbol": "SHORT_CALL",
            "expiration_date": "2025-01-24",
            "strike_price": "200",
            "type": "call",
        },
        {
            "symbol": "SHORT_PUT",
            "expiration_date": "2025-01-24",
            "strike_price": "200",
            "type": "put",
        },
        {
            "symbol": "LONG_CALL",
            "expiration_date": "2025-01-31",
            "strike_price": "200",
            "type": "call",
        },
        {
            "symbol": "LONG_PUT",
            "expiration_date": "2025-01-31",
            "strike_price": "200",
            "type": "put",
        },
    ]


def test_builds_historical_atm_volatility_pair_and_decomposition(
    monkeypatch,
) -> None:
    provider = make_provider()
    contracts = make_contracts()
    contracts_by_symbol = {contract["symbol"]: contract for contract in contracts}
    monkeypatch.setattr(
        provider,
        "_get_contracts_around_event",
        lambda symbol, earnings_date, expiry_search_days: contracts,
    )

    def get_bars(symbols, cutoff):
        bars = {}
        for contract_symbol in symbols:
            contract = contracts_by_symbol[contract_symbol]
            expiry = date.fromisoformat(contract["expiration_date"])
            volatility = 0.30 if contract_symbol.startswith("SHORT") else 0.45
            option = EuropeanOption(
                underlying="AAPL",
                strike=200.0,
                expiry=expiry,
                option_type=contract["type"],
            )
            price = black_scholes_price(
                option,
                MarketState(
                    spot=200.0,
                    volatility=volatility,
                    risk_free_rate=0.04,
                    dividend_yield=0.0,
                    valuation_date=cutoff.date(),
                ),
            )
            bars[contract_symbol] = HistoricalOptionBar(
                close=price,
                timestamp=cutoff - timedelta(minutes=1),
            )
        return bars

    monkeypatch.setattr(provider, "_get_pre_cutoff_bars", get_bars)
    monkeypatch.setattr(
        provider,
        "_get_pre_cutoff_stock_bar",
        lambda symbol, cutoff, stock_feed: HistoricalOptionBar(
            close=200.0,
            timestamp=cutoff - timedelta(minutes=1),
        ),
    )

    result = provider.get_earnings_variance(
        symbol=" aapl ",
        earnings_date=date(2025, 1, 30),
        release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
        price_provider=FakePriceProvider(),
        risk_free_rate=0.04,
    )

    assert result.symbol == "AAPL"
    assert result.observation_time == datetime(
        2025,
        1,
        15,
        15,
        55,
        tzinfo=result.observation_time.tzinfo,
    )
    assert result.short_expiry == date(2025, 1, 24)
    assert result.long_expiry == date(2025, 1, 31)
    assert result.short_call_symbol == "SHORT_CALL"
    assert result.long_put_symbol == "LONG_PUT"
    assert result.short_atm_iv == pytest.approx(0.30, abs=0.00001)
    assert result.long_atm_iv == pytest.approx(0.45, abs=0.00001)
    assert result.ordinary_implied_volatility == pytest.approx(0.30)
    assert result.earnings_implied_move == pytest.approx(
        (0.45**2 * 16 / 365 - 0.30**2 * 16 / 365) ** 0.5,
        abs=0.00001,
    )
    assert result.spot == 200.0
    assert result.spot_observation_time == (
        result.observation_time - timedelta(minutes=1)
    )
    assert result.source == ("alpaca_indicative_minute_bar_close_iv;stock_feed=iex")


def test_contract_query_covers_expiries_around_event(monkeypatch) -> None:
    provider = make_provider()
    captured = {}

    def get_json(url, params):
        captured.update(params)
        return {"option_contracts": make_contracts()}

    monkeypatch.setattr(provider, "_get_json", get_json)

    result = provider._get_contracts_around_event(
        symbol="AAPL",
        earnings_date=date(2025, 1, 30),
        expiry_search_days=21,
    )

    assert len(result) == 4
    assert captured["status"] == "inactive"
    assert captured["expiration_date_gte"] == "2025-01-09"
    assert captured["expiration_date_lte"] == "2025-02-20"


def test_contract_expiry_extraction_ignores_invalid_rows() -> None:
    expiries = make_provider()._contract_expiries(
        [
            {"expiration_date": "2025-01-24"},
            {"expiration_date": "not-a-date"},
            {},
        ]
    )

    assert expiries == {date(2025, 1, 24)}


def test_stock_bar_uses_raw_price_at_or_before_cutoff(monkeypatch) -> None:
    provider = make_provider()
    captured = {}

    def get_json(url, params):
        captured.update(params)
        return {
            "bars": {
                "AAPL": [
                    {"c": 201, "t": "2025-01-15T20:54:00Z"},
                    {"c": 202, "t": "2025-01-15T20:56:00Z"},
                ]
            }
        }

    monkeypatch.setattr(provider, "_get_json", get_json)
    cutoff = datetime(2025, 1, 15, 20, 55, tzinfo=timezone.utc)

    bar = provider._get_pre_cutoff_stock_bar("AAPL", cutoff, "iex")

    assert bar.close == 201
    assert captured["adjustment"] == "raw"
    assert captured["feed"] == "iex"
    assert captured["end"] == cutoff.isoformat()


def test_daily_stock_bars_supply_trading_sessions_without_yahoo(
    monkeypatch,
) -> None:
    provider = make_provider()
    captured = {}

    def get_json(url, params):
        captured.update(params)
        return {
            "bars": {
                "AAPL": [
                    {"c": 232.50, "t": "2025-01-14T05:00:00Z"},
                    {"c": 237.82, "t": "2025-01-15T05:00:00Z"},
                ]
            }
        }

    monkeypatch.setattr(provider, "_get_json", get_json)

    closes = provider._get_historical_stock_closes(
        symbol="AAPL",
        start_date=date(2025, 1, 14),
        end_date=date(2025, 1, 15),
        stock_feed="iex",
    )

    assert closes == {
        date(2025, 1, 14): 232.50,
        date(2025, 1, 15): 237.82,
    }
    assert captured["timeframe"] == "1Day"
    assert captured["adjustment"] == "raw"
    assert captured["feed"] == "iex"
    assert captured["end"] == "2025-01-16"


def test_stale_stock_bar_is_rejected(monkeypatch) -> None:
    provider = AlpacaHistoricalEarningsVarianceProvider(
        "key",
        "secret",
        max_staleness_minutes=30,
    )
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda url, params: {
            "bars": {
                "AAPL": [
                    {"c": 201, "t": "2025-01-15T19:00:00Z"},
                ]
            }
        },
    )

    with pytest.raises(ValueError, match="stale"):
        provider._get_pre_cutoff_stock_bar(
            "AAPL",
            datetime(2025, 1, 15, 20, 55, tzinfo=timezone.utc),
            "iex",
        )


@pytest.mark.parametrize("invalid_rate", [float("nan"), float("inf")])
def test_non_finite_interest_rate_is_rejected(invalid_rate: float) -> None:
    with pytest.raises(ValueError, match="Risk-free rate must be finite"):
        make_provider().get_earnings_variance(
            symbol="AAPL",
            earnings_date=date(2025, 1, 30),
            release_timing=EarningsReleaseTiming.AFTER_MARKET_CLOSE,
            price_provider=FakePriceProvider(),
            risk_free_rate=invalid_rate,
        )
