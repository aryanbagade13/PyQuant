from datetime import date
from typing import Any

from curl_cffi import requests

from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)


class NasdaqReleaseTimingProvider:
    """Retrieve pre-market/after-hours labels from Nasdaq's calendar."""

    BASE_URL = "https://api.nasdaq.com/api/calendar/earnings"

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout
        self._cache: dict[date, dict[str, Any]] = {}

    def get_release_timing(
        self,
        symbol: str,
        earnings_date: date,
    ) -> EarningsReleaseTiming:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        payload = self._cache.get(earnings_date)
        if payload is None:
            payload = self._request_json(earnings_date)
            self._cache[earnings_date] = payload

        for row in self._extract_rows(payload):
            row_symbol = str(row.get("symbol", "")).strip().upper()
            if row_symbol == symbol:
                raw_timing = (
                    row.get("time")
                    or row.get("reportTime")
                    or row.get("releaseTime")
                )
                return self._normalise_timing(raw_timing)

        return EarningsReleaseTiming.UNKNOWN

    def _request_json(self, earnings_date: date) -> dict[str, Any]:
        try:
            response = requests.get(
                self.BASE_URL,
                params={"date": earnings_date.isoformat()},
                headers={
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=self.timeout,
                impersonate="chrome",
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestsError, ValueError) as error:
            raise RuntimeError("Unable to retrieve Nasdaq earnings timing.") from error

        if not isinstance(payload, dict):
            raise RuntimeError("Nasdaq returned an invalid response.")
        return payload

    @staticmethod
    def _extract_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if data is None:
            return []
        if not isinstance(data, dict):
            raise RuntimeError("Nasdaq returned an invalid earnings calendar.")

        rows = data.get("rows")
        if rows is None:
            return []
        if not isinstance(rows, list) or not all(
            isinstance(row, dict) for row in rows
        ):
            raise RuntimeError("Nasdaq returned invalid earnings calendar rows.")
        return rows

    @staticmethod
    def _normalise_timing(value: object) -> EarningsReleaseTiming:
        if value is None:
            return EarningsReleaseTiming.UNKNOWN

        text = str(value).strip().lower().replace("_", "-")
        before_open = {
            "bmo",
            "before market open",
            "pre-market",
            "premarket",
            "time-pre-market",
        }
        after_close = {
            "amc",
            "after market close",
            "after hours",
            "after-hours",
            "time-after-hours",
        }
        if text in before_open:
            return EarningsReleaseTiming.BEFORE_MARKET_OPEN
        if text in after_close:
            return EarningsReleaseTiming.AFTER_MARKET_CLOSE
        return EarningsReleaseTiming.UNKNOWN
