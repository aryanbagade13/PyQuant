from dataclasses import dataclass, replace
from datetime import date

from pyquant.market.market_state import MarketState
from pyquant.market.option_quote import OptionQuote
from pyquant.pricing.greeks import delta, gamma, rho, theta, vega
from pyquant.pricing.implied_volatility import implied_volatility


@dataclass(frozen=True)
class OptionAnalysisRow:
    option_type: str
    strike: float
    bid: float
    ask: float
    mid_price: float
    spread: float|None
    moneyness: float
    implied_volatility: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


@dataclass(frozen=True)
class OptionChainAnalysis:
    symbol: str
    spot: float
    expiry: date
    rows: tuple[OptionAnalysisRow, ...]

    def calls(self) -> tuple[OptionAnalysisRow, ...]:
        return tuple(
            row
            for row in self.rows
            if str(row.option_type).lower() == "call"
        )

    def puts(self) -> tuple[OptionAnalysisRow, ...]:
        return tuple(
            row
            for row in self.rows
            if str(row.option_type).lower() == "put"
        )

    def at_the_money(self) -> OptionAnalysisRow:
        if not self.rows:
            raise ValueError(
                "Cannot find an at-the-money option in an empty analysis."
            )

        return min(
            self.rows,
            key=lambda row: abs(row.strike - self.spot),
        )

    def average_iv(self) -> float:
        if not self.rows:
            raise ValueError(
                "Cannot calculate average IV for an empty analysis."
            )

        return sum(
            row.implied_volatility
            for row in self.rows
        ) / len(self.rows)

    def highest_gamma(self) -> OptionAnalysisRow:
        if not self.rows:
            raise ValueError(
                "Cannot find highest gamma in an empty analysis."
            )

        return max(
            self.rows,
            key=lambda row: row.gamma,
        )


def analyse_option_quote(
    quote: OptionQuote,
    market: MarketState,
) -> OptionAnalysisRow:
    calculated_iv = implied_volatility(
        quote=quote,
        market=market,
    )

    calibrated_market = replace(
        market,
        volatility=calculated_iv,
    )

    option = quote.option

    return OptionAnalysisRow(
        option_type=str(option.option_type).lower(),
        strike=option.strike,
        bid=quote.bid,
        ask=quote.ask,
        mid_price=quote.mid_price,
        spread=quote.spread,
        moneyness=option.strike / market.spot,
        implied_volatility=calculated_iv,
        delta=delta(option, calibrated_market),
        gamma=gamma(option, calibrated_market),
        vega=vega(option, calibrated_market),
        theta=theta(option, calibrated_market),
        rho=rho(option, calibrated_market),
    )


def analyse_option_chain(
    symbol: str,
    expiry: date,
    quotes: tuple[OptionQuote, ...],
    market: MarketState,
) -> OptionChainAnalysis:
    rows: list[OptionAnalysisRow] = []

    for quote in quotes:
        try:
            market_price = quote.mid_price
        except ValueError:
            continue

        if market_price <= 0.0:
            continue

        try:
            row = analyse_option_quote(
                quote=quote,
                market=market,
            )
        except (
                ValueError,
                ZeroDivisionError,
                RuntimeError,
                OverflowError,
        ):
            continue

        rows.append(row)

    rows.sort(
        key=lambda row: (
            row.option_type,
            row.strike,
        )
    )

    return OptionChainAnalysis(
        symbol=symbol,
        spot=market.spot,
        expiry=expiry,
        rows=tuple(rows),
    )