from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from curl_cffi import requests

from pyquant.config import ALPACA_API_KEY, ALPACA_SECRET_KEY
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.models.implied_move import ImpliedMove
from pyquant.event_volatility.earnings_lab.calculations.pre_earnings_cutoff import (
    get_pre_earnings_cutoff,
)


NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class HistoricalOptionBar:
    close: float
    timestamp: datetime


class AlpacaHistoricalImpliedMoveProvider:
    """Estimate an event move from historical Alpaca option minute bars."""

    CONTRACTS_URL = "https://paper-api.alpaca.markets/v2/options/contracts"
    BARS_URL = "https://data.alpaca.markets/v1beta1/options/bars"

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        timeout: float = 20.0,
        max_staleness_minutes: float = 60.0,
    ) -> None:
        self.api_key = api_key or ALPACA_API_KEY
        self.secret_key = secret_key or ALPACA_SECRET_KEY
        self.timeout = timeout
        self.max_staleness_minutes = max_staleness_minutes
        if max_staleness_minutes < 0:
            raise ValueError("Maximum staleness cannot be negative.")
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials must be set.")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Accept": "application/json",
        }

    def get_implied_move(
        self,
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
        spot: float,
    ) -> ImpliedMove:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
        if spot <= 0:
            raise ValueError("Spot must be positive.")

        contracts = self._get_candidate_contracts(
            symbol, earnings_date, release_timing
        )
        call, put, strike = self._select_atm_pair(contracts, spot)
        cutoff = get_pre_earnings_cutoff(earnings_date, release_timing)
        bars = self._get_pre_cutoff_bars(
            [str(call["symbol"]), str(put["symbol"])], cutoff
        )
        call_symbol = str(call["symbol"])
        put_symbol = str(put["symbol"])
        return ImpliedMove(
            spot=spot,
            atm_strike=strike,
            call_mid=bars[call_symbol].close,
            put_mid=bars[put_symbol].close,
            expiry=date.fromisoformat(str(call["expiration_date"])),
            call_symbol=call_symbol,
            put_symbol=put_symbol,
            call_observation_time=bars[call_symbol].timestamp,
            put_observation_time=bars[put_symbol].timestamp,
            source="alpaca_indicative_minute_bar_close",
        )

    def _get_candidate_contracts(
        self,
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
    ) -> list[dict[str, Any]]:
        if release_timing == EarningsReleaseTiming.AFTER_MARKET_CLOSE:
            first_expiry = earnings_date + timedelta(days=1)
        elif release_timing == EarningsReleaseTiming.BEFORE_MARKET_OPEN:
            first_expiry = earnings_date
        else:
            raise ValueError("A known before-open or after-close timing is required.")

        params: dict[str, object] = {
            "underlying_symbols": symbol,
            "status": "inactive",
            "expiration_date_gte": first_expiry.isoformat(),
            "expiration_date_lte": (first_expiry + timedelta(days=14)).isoformat(),
            "limit": 10000,
        }
        payload = self._get_json(self.CONTRACTS_URL, params)
        contracts = payload.get("option_contracts")
        if not isinstance(contracts, list) or not contracts:
            raise ValueError(f"No historical option contracts found for {symbol}.")

        expiries = sorted(
            {
                date.fromisoformat(str(contract["expiration_date"]))
                for contract in contracts
                if isinstance(contract, dict) and contract.get("expiration_date")
            }
        )
        if not expiries:
            raise ValueError(f"No usable option expiries found for {symbol}.")
        chosen_expiry = expiries[0]
        return [
            contract
            for contract in contracts
            if isinstance(contract, dict)
            and str(contract.get("expiration_date")) == chosen_expiry.isoformat()
        ]

    @staticmethod
    def _select_atm_pair(
        contracts: list[dict[str, Any]],
        spot: float,
    ) -> tuple[dict[str, Any], dict[str, Any], float]:
        pairs: dict[float, dict[str, dict[str, Any]]] = {}
        for contract in contracts:
            try:
                strike = float(contract["strike_price"])
                option_type = str(contract["type"]).lower()
                contract_symbol = str(contract["symbol"])
            except (KeyError, TypeError, ValueError):
                continue
            if strike <= 0 or option_type not in {"call", "put"} or not contract_symbol:
                continue
            pairs.setdefault(strike, {})[option_type] = contract

        complete = {
            strike: pair
            for strike, pair in pairs.items()
            if "call" in pair and "put" in pair
        }
        if not complete:
            raise ValueError("No strike has both a call and put contract.")
        strike = min(complete, key=lambda value: abs(value - spot))
        return complete[strike]["call"], complete[strike]["put"], strike

    def _get_pre_cutoff_bars(
        self,
        symbols: list[str],
        cutoff: datetime,
    ) -> dict[str, HistoricalOptionBar]:
        session_start = datetime.combine(
            cutoff.date(), time(9, 30), tzinfo=NEW_YORK
        )
        payload = self._get_json(
            self.BARS_URL,
            {
                "symbols": ",".join(symbols),
                "timeframe": "1Min",
                "start": session_start.isoformat(),
                "end": cutoff.isoformat(),
                "limit": 10000,
                "sort": "desc",
            },
        )
        bars = payload.get("bars")
        if not isinstance(bars, dict):
            raise ValueError("Alpaca returned no historical option bars.")

        selected: dict[str, HistoricalOptionBar] = {}
        for symbol in symbols:
            symbol_bars = bars.get(symbol)
            if not isinstance(symbol_bars, list) or not symbol_bars:
                raise ValueError(f"No pre-cutoff option bars found for {symbol}.")

            eligible: list[HistoricalOptionBar] = []
            for bar in symbol_bars:
                try:
                    timestamp = datetime.fromisoformat(
                        str(bar["t"]).replace("Z", "+00:00")
                    )
                    close = float(bar["c"])
                except (KeyError, TypeError, ValueError):
                    continue
                if timestamp.tzinfo is None:
                    raise ValueError("Historical option bar timestamp must be timezone-aware.")
                if timestamp <= cutoff and close > 0:
                    eligible.append(HistoricalOptionBar(close, timestamp))

            if not eligible:
                raise ValueError(f"No valid pre-cutoff option bars found for {symbol}.")
            latest = max(eligible, key=lambda bar: bar.timestamp)
            age_minutes = (cutoff - latest.timestamp).total_seconds() / 60
            if age_minutes > self.max_staleness_minutes:
                raise ValueError(
                    f"Historical option bar for {symbol} is "
                    f"{age_minutes:.1f} minutes stale."
                )
            selected[symbol] = latest
        return selected

    def _get_json(
        self,
        url: str,
        params: dict[str, object],
    ) -> dict[str, Any]:
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self.timeout,
                impersonate="chrome",
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestsError as error:
            detail = ""
            response = getattr(error, "response", None)
            if response is not None:
                detail = f" {response.text[:500]}"
            raise RuntimeError(f"Alpaca request failed for {url}.{detail}") from error
        except ValueError as error:
            raise RuntimeError(f"Alpaca returned invalid JSON for {url}.") from error
        if not isinstance(payload, dict):
            raise RuntimeError("Alpaca returned an invalid response.")
        return payload
