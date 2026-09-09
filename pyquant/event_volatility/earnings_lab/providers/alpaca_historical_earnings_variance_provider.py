import math
from datetime import date, datetime, time, timedelta
from typing import Any

from pyquant.event_volatility.earnings_lab.calculations.earnings_variance import (
    decompose_earnings_variance,
)
from pyquant.event_volatility.earnings_lab.calculations.option_observation_cutoff import (
    select_option_observation_cutoff,
)
from pyquant.event_volatility.earnings_lab.calculations.pre_earnings_cutoff import (
    NEW_YORK,
)
from pyquant.event_volatility.earnings_lab.earnings_expiry_window import (
    EarningsExpiryWindow,
)
from pyquant.event_volatility.earnings_lab.models.earnings_release_timing import (
    EarningsReleaseTiming,
)
from pyquant.event_volatility.earnings_lab.models.historical_earnings_variance import (
    HistoricalEarningsVarianceEstimate,
)
from pyquant.event_volatility.earnings_lab.providers.alpaca_historical_implied_move_provider import (
    AlpacaHistoricalImpliedMoveProvider,
    HistoricalOptionBar,
)
from pyquant.event_volatility.earnings_lab.providers.historical_price_provider import (
    HistoricalPriceProvider,
)
from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.pricing.implied_volatility import implied_volatility


class AlpacaHistoricalEarningsVarianceProvider(AlpacaHistoricalImpliedMoveProvider):
    """Estimate earnings variance from two historical Alpaca expiries."""

    SOURCE = "alpaca_indicative_minute_bar_close_iv"
    STOCK_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"

    def get_earnings_variance(
        self,
        symbol: str,
        earnings_date: date,
        release_timing: EarningsReleaseTiming,
        risk_free_rate: float,
        price_provider: HistoricalPriceProvider | None = None,
        dividend_yield: float = 0.0,
        trading_sessions_before_earnings: int = 10,
        expiry_search_days: int = 21,
        stock_feed: str = "iex",
    ) -> HistoricalEarningsVarianceEstimate:
        """Build an auditable short/long-expiry earnings-variance estimate."""
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
        if not math.isfinite(risk_free_rate):
            raise ValueError("Risk-free rate must be finite.")
        if not math.isfinite(dividend_yield):
            raise ValueError("Dividend yield must be finite.")
        if stock_feed not in {"iex", "sip"}:
            raise ValueError("Stock feed must be 'iex' or 'sip'.")

        contracts = self._get_contracts_around_event(
            symbol=symbol,
            earnings_date=earnings_date,
            expiry_search_days=expiry_search_days,
        )
        expiries = self._contract_expiries(contracts)
        expiry_window = EarningsExpiryWindow.from_expiries(
            expiries=expiries,
            symbol=symbol,
            earnings_date=earnings_date,
            release_timing=release_timing,
        )
        cutoff_provider = price_provider or _AlpacaStockPriceProvider(
            owner=self,
            stock_feed=stock_feed,
        )
        cutoff = select_option_observation_cutoff(
            provider=cutoff_provider,
            symbol=symbol,
            earnings_date=earnings_date,
            expiry_window=expiry_window,
            trading_sessions_before_earnings=(trading_sessions_before_earnings),
        )
        spot_bar = self._get_pre_cutoff_stock_bar(
            symbol=symbol,
            cutoff=cutoff,
            stock_feed=stock_feed,
        )
        spot = spot_bar.close

        short_contracts = self._contracts_for_expiry(
            contracts,
            expiry_window.short_expiry,
        )
        long_contracts = self._contracts_for_expiry(
            contracts,
            expiry_window.long_expiry,
        )
        short_call, short_put, short_strike = self._select_atm_pair(
            short_contracts,
            spot,
        )
        long_call, long_put, long_strike = self._select_atm_pair(
            long_contracts,
            spot,
        )

        selected_contracts = (
            short_call,
            short_put,
            long_call,
            long_put,
        )
        symbols = [str(contract["symbol"]) for contract in selected_contracts]
        bars = self._get_pre_cutoff_bars(symbols, cutoff)

        short_call_iv = self._calculate_bar_iv(
            symbol,
            short_call,
            bars[str(short_call["symbol"])],
            spot,
            cutoff.date(),
            risk_free_rate,
            dividend_yield,
        )
        short_put_iv = self._calculate_bar_iv(
            symbol,
            short_put,
            bars[str(short_put["symbol"])],
            spot,
            cutoff.date(),
            risk_free_rate,
            dividend_yield,
        )
        long_call_iv = self._calculate_bar_iv(
            symbol,
            long_call,
            bars[str(long_call["symbol"])],
            spot,
            cutoff.date(),
            risk_free_rate,
            dividend_yield,
        )
        long_put_iv = self._calculate_bar_iv(
            symbol,
            long_put,
            bars[str(long_put["symbol"])],
            spot,
            cutoff.date(),
            risk_free_rate,
            dividend_yield,
        )

        short_atm_iv = (short_call_iv + short_put_iv) / 2.0
        long_atm_iv = (long_call_iv + long_put_iv) / 2.0
        decomposition = decompose_earnings_variance(
            valuation_date=cutoff.date(),
            expiry_window=expiry_window,
            short_implied_volatility=short_atm_iv,
            long_implied_volatility=long_atm_iv,
        )

        return HistoricalEarningsVarianceEstimate(
            symbol=symbol,
            observation_time=cutoff,
            spot=spot,
            spot_observation_time=spot_bar.timestamp,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            short_atm_strike=short_strike,
            short_call_symbol=str(short_call["symbol"]),
            short_put_symbol=str(short_put["symbol"]),
            short_call_price=bars[str(short_call["symbol"])].close,
            short_put_price=bars[str(short_put["symbol"])].close,
            short_call_iv=short_call_iv,
            short_put_iv=short_put_iv,
            short_call_observation_time=(bars[str(short_call["symbol"])].timestamp),
            short_put_observation_time=(bars[str(short_put["symbol"])].timestamp),
            long_atm_strike=long_strike,
            long_call_symbol=str(long_call["symbol"]),
            long_put_symbol=str(long_put["symbol"]),
            long_call_price=bars[str(long_call["symbol"])].close,
            long_put_price=bars[str(long_put["symbol"])].close,
            long_call_iv=long_call_iv,
            long_put_iv=long_put_iv,
            long_call_observation_time=(bars[str(long_call["symbol"])].timestamp),
            long_put_observation_time=(bars[str(long_put["symbol"])].timestamp),
            decomposition=decomposition,
            source=f"{self.SOURCE};stock_feed={stock_feed}",
        )

    def _get_historical_stock_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        stock_feed: str,
        adjustment: str = "raw",
    ) -> dict[date, float]:
        """Return raw daily closes without importing pandas or yfinance."""
        end_exclusive = end_date + timedelta(days=1)
        payload = self._get_json(
            self.STOCK_BARS_URL,
            {
                "symbols": symbol,
                "timeframe": "1Day",
                "start": start_date.isoformat(),
                "end": end_exclusive.isoformat(),
                "limit": 10000,
                "adjustment": adjustment,
                "feed": stock_feed,
                "sort": "asc",
            },
        )
        bars = payload.get("bars")
        if not isinstance(bars, dict):
            raise ValueError("Alpaca returned no historical daily stock bars.")
        symbol_bars = bars.get(symbol)
        if not isinstance(symbol_bars, list) or not symbol_bars:
            raise ValueError(f"No historical daily stock bars found for {symbol}.")

        closes: dict[date, float] = {}
        for raw_bar in symbol_bars:
            try:
                trading_date = datetime.fromisoformat(
                    str(raw_bar["t"]).replace("Z", "+00:00")
                ).date()
                close = float(raw_bar["c"])
            except (KeyError, TypeError, ValueError):
                continue
            if (
                start_date <= trading_date <= end_date
                and math.isfinite(close)
                and close > 0
            ):
                closes[trading_date] = close
        if not closes:
            raise ValueError(
                f"No valid historical daily stock bars found for {symbol}."
            )
        return closes

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        """Return split-adjusted Alpaca closes for realised-return research."""
        return self._get_historical_stock_closes(
            symbol=symbol.strip().upper(),
            start_date=start_date,
            end_date=end_date,
            stock_feed="iex",
            adjustment="all",
        )

    def _get_contracts_around_event(
        self,
        symbol: str,
        earnings_date: date,
        expiry_search_days: int,
    ) -> list[dict[str, Any]]:
        if expiry_search_days < 1:
            raise ValueError("Expiry search days must be positive.")

        payload = self._get_json(
            self.CONTRACTS_URL,
            {
                "underlying_symbols": symbol,
                "status": "inactive",
                "expiration_date_gte": (
                    earnings_date - timedelta(days=expiry_search_days)
                ).isoformat(),
                "expiration_date_lte": (
                    earnings_date + timedelta(days=expiry_search_days)
                ).isoformat(),
                "limit": 10000,
            },
        )
        contracts = payload.get("option_contracts")
        if not isinstance(contracts, list) or not contracts:
            raise ValueError(f"No historical option contracts found for {symbol}.")
        return [contract for contract in contracts if isinstance(contract, dict)]

    @staticmethod
    def _contract_expiries(
        contracts: list[dict[str, Any]],
    ) -> set[date]:
        expiries: set[date] = set()
        for contract in contracts:
            try:
                expiries.add(date.fromisoformat(str(contract["expiration_date"])))
            except (KeyError, TypeError, ValueError):
                continue
        return expiries

    @staticmethod
    def _contracts_for_expiry(
        contracts: list[dict[str, Any]],
        expiry: date,
    ) -> list[dict[str, Any]]:
        matching = [
            contract
            for contract in contracts
            if str(contract.get("expiration_date")) == expiry.isoformat()
        ]
        if not matching:
            raise ValueError(
                f"No historical option contracts found for expiry {expiry}."
            )
        return matching

    def _get_pre_cutoff_stock_bar(
        self,
        symbol: str,
        cutoff: datetime,
        stock_feed: str,
    ) -> HistoricalOptionBar:
        session_start = datetime.combine(
            cutoff.date(),
            time(hour=9, minute=30),
            tzinfo=NEW_YORK,
        )
        payload = self._get_json(
            self.STOCK_BARS_URL,
            {
                "symbols": symbol,
                "timeframe": "1Min",
                "start": session_start.isoformat(),
                "end": cutoff.isoformat(),
                "limit": 10000,
                "adjustment": "raw",
                "feed": stock_feed,
                "sort": "desc",
            },
        )
        bars = payload.get("bars")
        if not isinstance(bars, dict):
            raise ValueError("Alpaca returned no historical stock bars.")
        symbol_bars = bars.get(symbol)
        if not isinstance(symbol_bars, list) or not symbol_bars:
            raise ValueError(f"No historical stock bars found for {symbol}.")

        candidates: list[HistoricalOptionBar] = []
        for raw_bar in symbol_bars:
            try:
                timestamp = datetime.fromisoformat(
                    str(raw_bar["t"]).replace("Z", "+00:00")
                )
                close = float(raw_bar["c"])
            except (KeyError, TypeError, ValueError):
                continue
            if timestamp.tzinfo is None:
                continue
            if timestamp <= cutoff and math.isfinite(close) and close > 0:
                candidates.append(HistoricalOptionBar(close=close, timestamp=timestamp))

        if not candidates:
            raise ValueError(f"No valid pre-cutoff stock bar found for {symbol}.")
        selected = max(candidates, key=lambda bar: bar.timestamp)
        staleness_minutes = (cutoff - selected.timestamp).total_seconds() / 60.0
        if staleness_minutes > self.max_staleness_minutes:
            raise ValueError(
                f"Alpaca stock bar for {symbol} is stale by "
                f"{staleness_minutes:.1f} minutes."
            )
        return selected

    @staticmethod
    def _calculate_bar_iv(
        symbol: str,
        contract: dict[str, Any],
        bar: HistoricalOptionBar,
        spot: float,
        valuation_date: date,
        risk_free_rate: float,
        dividend_yield: float,
    ) -> float:
        try:
            option = EuropeanOption(
                underlying=symbol,
                strike=float(contract["strike_price"]),
                expiry=date.fromisoformat(str(contract["expiration_date"])),
                option_type=str(contract["type"]).lower(),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Historical option contract is invalid.") from error

        quote = OptionQuote(
            option=option,
            bid=bar.close,
            ask=bar.close,
            last_trade_time=bar.timestamp,
        )
        market = MarketState(
            spot=spot,
            volatility=0.20,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            valuation_date=valuation_date,
        )
        try:
            return implied_volatility(quote=quote, market=market)
        except (ValueError, ZeroDivisionError, RuntimeError) as error:
            contract_symbol = str(contract.get("symbol", "unknown"))
            raise ValueError(
                f"Could not calculate implied volatility for {contract_symbol}: {error}"
            ) from error


class _AlpacaStockPriceProvider:
    """Adapt Alpaca daily bars to the cutoff selector's small interface."""

    def __init__(
        self,
        owner: AlpacaHistoricalEarningsVarianceProvider,
        stock_feed: str,
    ) -> None:
        self.owner = owner
        self.stock_feed = stock_feed

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        return self.owner._get_historical_stock_closes(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            stock_feed=self.stock_feed,
        )
