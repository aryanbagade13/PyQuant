from datetime import date, datetime, timezone
from pyquant.data.market_snapshot import MarketSnapshot

import pandas as pd
import yfinance as yf

from pyquant.instruments.european_option import EuropeanOption
from pyquant.market.option_quote import OptionQuote


class YahooFinanceProvider:
    def get_spot(
        self,
        symbol: str,
    ) -> float:
        ticker = yf.Ticker(symbol)

        history = ticker.history(period="1d")

        if history.empty:
            raise ValueError(
                f"No price data returned for {symbol}."
            )

        spot = float(history["Close"].iloc[-1])

        if spot <= 0:
            raise ValueError(
                f"Invalid spot price returned for {symbol}: {spot}"
            )

        return spot

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

        chain = ticker.option_chain(
            expiry.isoformat()
        )

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

            if strike <= 0:
                continue

            if bid < 0 or ask < 0:
                continue

            if ask < bid:
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