import json
import ssl
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import certifi

from pyquant.config import ALPHA_VANTAGE_API_KEY
from pyquant.event_volatility.earnings_lab.models.earnings_report import (
    EarningsReport,
)


class AlphaVantageEarningsProvider:
    """Retrieve historical quarterly EPS reports from Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or ALPHA_VANTAGE_API_KEY
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY must be set.")

    def get_historical_earnings(self, symbol: str) -> list[EarningsReport]:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        payload = self._request_json(symbol)
        raw_reports = payload.get("quarterlyEarnings")
        if not isinstance(raw_reports, list):
            message = payload.get("Note") or payload.get("Information")
            if message:
                raise RuntimeError(f"Alpha Vantage request failed: {message}")
            raise RuntimeError("Alpha Vantage returned no quarterly earnings data.")

        reports = [self._parse_report(symbol, item) for item in raw_reports]
        reports.sort(key=lambda report: report.reported_date)
        return reports

    def _request_json(self, symbol: str) -> dict[str, Any]:
        query = urlencode(
            {"function": "EARNINGS", "symbol": symbol, "apikey": self.api_key}
        )
        try:
            with urlopen(
                f"{self.BASE_URL}?{query}",
                timeout=self.timeout,
                context=ssl.create_default_context(cafile=certifi.where()),
            ) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError("Unable to retrieve Alpha Vantage earnings.") from error

        if not isinstance(payload, dict):
            raise RuntimeError("Alpha Vantage returned an invalid response.")
        return payload

    @staticmethod
    def _parse_report(symbol: str, item: object) -> EarningsReport:
        if not isinstance(item, dict):
            raise RuntimeError("Alpha Vantage returned an invalid earnings row.")
        try:
            return EarningsReport(
                symbol=symbol,
                reported_date=date.fromisoformat(str(item["reportedDate"])),
                fiscal_period_end=date.fromisoformat(
                    str(item["fiscalDateEnding"])
                ),
                estimated_eps=_optional_float(item.get("estimatedEPS")),
                actual_eps=_optional_float(item.get("reportedEPS")),
                provider_surprise=_optional_float(item.get("surprise")),
                provider_surprise_percentage=_optional_float(
                    item.get("surprisePercentage")
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Alpha Vantage returned an invalid earnings row.") from error


def _optional_float(value: object) -> float | None:
    if value is None or str(value).strip().lower() in {"", "none", "null", "-"}:
        return None
    return float(value)
