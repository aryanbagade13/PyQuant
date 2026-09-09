from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import (
    OptionChainRequest,
    StockLatestTradeRequest,
)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest

from pyquant.config import ALPACA_API_KEY, ALPACA_SECRET_KEY
from pyquant.data.market_snapshot import MarketSnapshot
from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.option_quote import OptionQuote


class AlpacaProvider:
    CACHE_DIRECTORY = Path("data_cache")
    EXPIRY_CACHE_DIRECTORY = CACHE_DIRECTORY / "expiries"

    def __init__(self) -> None:
        if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set.")

        self.stock_client = StockHistoricalDataClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
        )

        self.option_client = OptionHistoricalDataClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
        )

        # Used to retrieve available option contracts and expiries.
        self.trading_client = TradingClient(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            paper=True,
        )

    def _expiry_cache_path(
        self,
        symbol: str,
    ) -> Path:
        self.EXPIRY_CACHE_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        return self.EXPIRY_CACHE_DIRECTORY / f"{symbol.upper()}.csv"

    def get_spot(
        self,
        symbol: str,
    ) -> float:
        symbol = symbol.upper().strip()

        request = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
        )

        trades = self.stock_client.get_stock_latest_trade(request)

        trade = trades.get(symbol)

        if trade is None:
            raise ValueError(f"No latest stock trade returned for {symbol}.")

        spot = float(trade.price)

        if spot <= 0:
            raise ValueError(f"Invalid spot price returned for {symbol}: {spot}")

        return spot

    def _save_expiry_cache(
        self,
        symbol: str,
        expiries: list[date],
    ) -> None:
        path = self._expiry_cache_path(symbol)

        pd.Series(expiries).astype(str).to_csv(
            path,
            index=False,
            header=False,
        )

    def _load_expiry_cache(
        self,
        symbol: str,
    ) -> list[date] | None:
        path = self._expiry_cache_path(symbol)

        if not path.exists():
            return None

        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)

        if age > timedelta(days=1):
            return None

        dataframe = pd.read_csv(
            path,
            header=None,
        )

        return [date.fromisoformat(value) for value in dataframe[0]]

    def get_expiries(
        self,
        symbol: str,
    ) -> list[date]:
        """
        Return all available option expiry dates
        for an underlying symbol.
        """
        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        cached = self._load_expiry_cache(symbol)

        if cached is not None:
            return cached

        today = date.today()
        final_date = today + timedelta(days=365)

        expiries: set[date] = set()
        page_token: str | None = None

        while True:
            request = GetOptionContractsRequest(
                underlying_symbols=[symbol],
                expiration_date_gte=today,
                expiration_date_lte=final_date,
                limit=10_000,
                page_token=page_token,
            )

            response = self.trading_client.get_option_contracts(request)

            contracts = response.option_contracts

            for contract in contracts:
                expiry = contract.expiration_date

                if isinstance(expiry, str):
                    expiry = date.fromisoformat(expiry)

                expiries.add(expiry)

            page_token = response.next_page_token

            if not page_token:
                break

        sorted_expiries = sorted(expiries)

        self._save_expiry_cache(
            symbol=symbol,
            expiries=sorted_expiries,
        )

        return sorted_expiries

    def get_option_chain(
        self,
        symbol: str,
        expiry: date,
    ) -> list[OptionQuote]:
        """
        Download one Alpaca option chain and convert it
        into pyquant OptionQuote objects.
        """
        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError("Symbol cannot be empty.")

        request = OptionChainRequest(
            underlying_symbol=symbol,
            expiration_date=expiry,
        )

        chain = self.option_client.get_option_chain(request)

        if not chain:
            raise ValueError(
                f"Alpaca returned no option contracts for "
                f"{symbol} with expiry {expiry}."
            )

        option_quotes: list[OptionQuote] = []

        missing_everything = 0
        invalid_prices = 0

        for contract_symbol, alpaca_snapshot in chain.items():
            quote = alpaca_snapshot.latest_quote
            trade = alpaca_snapshot.latest_trade

            if quote is None and trade is None:
                missing_everything += 1
                continue

            option = self._parse_contract_symbol(
                contract_symbol=contract_symbol,
                underlying=symbol,
            )

            bid = self._positive_float_or_zero(
                quote.bid_price if quote is not None else None
            )

            ask = self._positive_float_or_zero(
                quote.ask_price if quote is not None else None
            )

            last_price = self._positive_float_or_none(
                trade.price if trade is not None else None
            )

            last_trade_time = trade.timestamp if trade is not None else None

            has_valid_midpoint = bid > 0 and ask > 0

            has_valid_last_price = last_price is not None

            if not has_valid_midpoint and not has_valid_last_price:
                invalid_prices += 1
                continue

            option_quotes.append(
                OptionQuote(
                    option=option,
                    bid=bid,
                    ask=ask,
                    last_price=last_price,
                    last_trade_time=last_trade_time,
                )
            )

        if not option_quotes:
            raise ValueError(
                f"Alpaca returned {len(chain)} contracts for "
                f"{symbol} with expiry {expiry}, but none contained "
                f"usable market data. "
                f"{missing_everything} had no quote or trade and "
                f"{invalid_prices} had no valid price."
            )

        return option_quotes

    def get_snapshot(
        self,
        symbol: str,
        expiry: date,
    ) -> MarketSnapshot:
        """
        Build a MarketSnapshot containing the latest stock price
        and usable option quotes for one expiry.
        """
        symbol = symbol.upper().strip()

        spot = self.get_spot(symbol)

        option_quotes = self.get_option_chain(
            symbol=symbol,
            expiry=expiry,
        )

        return MarketSnapshot(
            symbol=symbol,
            spot=spot,
            timestamp=datetime.now(timezone.utc),
            option_quotes=tuple(option_quotes),
        )

    def _parse_contract_symbol(
        self,
        contract_symbol: str,
        underlying: str,
    ) -> EuropeanOption:
        """
        Parse an OCC-style option symbol such as:

        AAPL260731C00200000

        into an internal EuropeanOption.
        """
        if not contract_symbol.startswith(underlying):
            raise ValueError(
                f"Contract {contract_symbol} does not match underlying {underlying}."
            )

        contract_details = contract_symbol[len(underlying) :]

        if len(contract_details) != 15:
            raise ValueError(
                f"Unexpected Alpaca option symbol format: {contract_symbol}"
            )

        expiry_text = contract_details[:6]
        option_type_code = contract_details[6]
        strike_text = contract_details[7:]

        expiry = datetime.strptime(
            expiry_text,
            "%y%m%d",
        ).date()

        if option_type_code == "C":
            option_type = "call"

        elif option_type_code == "P":
            option_type = "put"

        else:
            raise ValueError(
                f"Unknown option type code {option_type_code!r} in {contract_symbol}."
            )

        try:
            strike = int(strike_text) / 1000

        except ValueError as error:
            raise ValueError(
                f"Invalid strike in contract symbol: {contract_symbol}"
            ) from error

        return EuropeanOption(
            underlying=underlying,
            strike=strike,
            expiry=expiry,
            option_type=option_type,
        )

    @staticmethod
    def _positive_float_or_zero(
        value: object,
    ) -> float:
        """
        Convert a value to a positive float,
        otherwise return zero.
        """
        if value is None:
            return 0.0

        try:
            converted = float(value)

        except (TypeError, ValueError):
            return 0.0

        return converted if converted > 0 else 0.0

    @staticmethod
    def _positive_float_or_none(
        value: object,
    ) -> float | None:
        """
        Convert a value to a positive float,
        otherwise return None.
        """
        if value is None:
            return None

        try:
            converted = float(value)

        except (TypeError, ValueError):
            return None

        return converted if converted > 0 else None
