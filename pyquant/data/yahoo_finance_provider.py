from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from pyquant.data.market_snapshot import MarketSnapshot
from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.option_quote import OptionQuote


class YahooFinanceProvider:
    CACHE_DIRECTORY = Path("data_cache")

    def get_spot(
        self,
        symbol: str,
    ) -> float:
        ticker = yf.Ticker(symbol)

        history = ticker.history(period="1d")

        if history.empty:
            raise ValueError(f"No price data returned for {symbol}.")

        spot = float(history["Close"].iloc[-1])

        if spot <= 0:
            raise ValueError(f"Invalid spot price returned for {symbol}: {spot}")

        return spot

    def get_historical_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        """Return adjusted daily closes for the inclusive date range."""
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date.")

        # yfinance treats end as exclusive, so request one extra day.
        history = yf.download(
            symbol,
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            auto_adjust=True,
            progress=False,
        )
        if history.empty or "Close" not in history:
            raise ValueError(f"No historical price data returned for {symbol}.")

        close_series = history["Close"]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]

        prices: dict[date, float] = {}
        for timestamp, value in close_series.dropna().items():
            trading_date = pd.Timestamp(timestamp).date()
            close = float(value)
            if close > 0:
                prices[trading_date] = close
        return prices

    def get_historical_raw_closes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[date, float]:
        """Return unadjusted closes for matching with historical derivatives."""
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date.")

        history = yf.download(
            symbol,
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            auto_adjust=False,
            progress=False,
        )
        if history.empty or "Close" not in history:
            raise ValueError(f"No historical raw prices returned for {symbol}.")

        close_series = history["Close"]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.iloc[:, 0]
        return {
            pd.Timestamp(timestamp).date(): float(value)
            for timestamp, value in close_series.dropna().items()
            if float(value) > 0
        }

    def get_expiries(
        self,
        symbol: str,
    ) -> list[date]:
        ticker = yf.Ticker(symbol)

        return [
            datetime.strptime(
                expiry,
                "%Y-%m-%d",
            ).date()
            for expiry in ticker.options
        ]

    def get_option_chain(
        self,
        symbol: str,
        expiry: date,
    ) -> list[OptionQuote]:
        ticker = yf.Ticker(symbol)

        chain = ticker.option_chain(expiry.isoformat())

        quotes: list[OptionQuote] = []

        quotes.extend(
            self._build_quotes(
                symbol=symbol,
                expiry=expiry,
                option_type="call",
                data=chain.calls,
            )
        )

        quotes.extend(
            self._build_quotes(
                symbol=symbol,
                expiry=expiry,
                option_type="put",
                data=chain.puts,
            )
        )

        return quotes

    def _save_chain(
        self,
        symbol: str,
        expiry: date,
        calls: pd.DataFrame,
        puts: pd.DataFrame,
    ) -> None:
        self.CACHE_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True,
        )

        cache_prefix = self.CACHE_DIRECTORY / f"{symbol}_{expiry.isoformat()}"

        calls.to_csv(
            f"{cache_prefix}_calls.csv",
            index=False,
        )

        puts.to_csv(
            f"{cache_prefix}_puts.csv",
            index=False,
        )

    def _load_chain(
        self,
        symbol: str,
        expiry: date,
    ) -> tuple[pd.DataFrame, pd.DataFrame] | None:
        cache_prefix = self.CACHE_DIRECTORY / f"{symbol}_{expiry.isoformat()}"

        calls_path = Path(f"{cache_prefix}_calls.csv")

        puts_path = Path(f"{cache_prefix}_puts.csv")

        if not calls_path.exists() or not puts_path.exists():
            return None

        calls = pd.read_csv(calls_path)
        puts = pd.read_csv(puts_path)

        return calls, puts

    def _build_quotes(
        self,
        symbol: str,
        expiry: date,
        option_type: str,
        data: pd.DataFrame,
    ) -> list[OptionQuote]:
        quotes: list[OptionQuote] = []

        for _, row in data.iterrows():
            strike = float(row["strike"])
            bid = float(row["bid"])
            ask = float(row["ask"])
            last_price = float(row["lastPrice"])

            last_trade_time: datetime | None = None

            raw_last_trade_time = row.get("lastTradeDate")

            if raw_last_trade_time is not None and not pd.isna(raw_last_trade_time):
                parsed_last_trade_time = pd.to_datetime(
                    raw_last_trade_time,
                    utc=True,
                )

                last_trade_time = parsed_last_trade_time.to_pydatetime()

            if strike <= 0:
                continue

            if bid < 0 or ask < 0:
                continue

            if ask < bid:
                continue

            if bid == 0.0 and ask == 0.0 and last_price <= 0.0:
                continue

            option = EuropeanOption(
                underlying=symbol,
                strike=strike,
                expiry=expiry,
                option_type=option_type,
            )

            quote = OptionQuote(
                option=option,
                bid=bid,
                ask=ask,
                last_price=last_price,
                last_trade_time=last_trade_time,
            )

            quotes.append(quote)

        return quotes

    def get_snapshot(
        self,
        symbol: str,
        expiry: date,
    ) -> MarketSnapshot:
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
