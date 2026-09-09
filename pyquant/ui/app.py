from datetime import date, timedelta
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from pyquant.analysis.option_chain_analysis import analyse_option_chain
from pyquant.analysis.volatility_surface import build_volatility_surface
from pyquant.data.alpaca_provider import AlpacaProvider
from pyquant.market.market_state import MarketState
from pyquant.visualisation.volatility_surface_3d import plot_volatility_surface

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="pyquant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        [data-testid="stSidebar"] {
            min-width: 310px;
            max-width: 310px;
        }

        .app-header {
            margin-bottom: 1.5rem;
        }

        .app-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0;
        }

        .app-subtitle {
            color: #7f8c8d;
            font-size: 1rem;
            margin-top: 0.2rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.20);
            border-radius: 0.7rem;
            padding: 1rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(128, 128, 128, 0.20);
            border-radius: 0.7rem;
            overflow: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Provider and cached data
# ---------------------------------------------------------------------


@st.cache_resource
def get_provider() -> AlpacaProvider:
    return AlpacaProvider()


@st.cache_data(ttl=900, show_spinner=False)
def load_expiries(symbol: str) -> list[date]:
    return get_provider().get_expiries(symbol)


@st.cache_data(ttl=60, show_spinner=False)
def load_snapshot(symbol: str, expiry: date):
    return get_provider().get_snapshot(
        symbol=symbol,
        expiry=expiry,
    )


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def load_option_analysis(
    symbol: str,
    expiry: date,
    risk_free_rate: float,
    dividend_yield: float,
):
    snapshot = load_snapshot(
        symbol=symbol,
        expiry=expiry,
    )

    market = create_market_state(
        spot=snapshot.spot,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
    )

    return analyse_option_chain(
        symbol=snapshot.symbol,
        expiry=expiry,
        quotes=snapshot.option_quotes,
        market=market,
    )


def create_market_state(
    spot: float,
    risk_free_rate: float,
    dividend_yield: float,
) -> MarketState:
    return MarketState(
        spot=spot,
        volatility=0.20,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        valuation_date=date.today(),
    )


# ---------------------------------------------------------------------
# General utility functions
# ---------------------------------------------------------------------


def get_first_attribute(
    obj: object | None,
    names: list[str],
    default: Any = None,
) -> Any:
    if obj is None:
        return default

    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)

            if value is not None:
                return value

    return default


def normalise_option_type(value: object) -> str:
    if hasattr(value, "value"):
        value = value.value

    text = str(value).lower().strip()

    if "call" in text:
        return "call"

    if "put" in text:
        return "put"

    return text


def safe_float(value: object) -> float | None:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(number):
        return None

    return number


# ---------------------------------------------------------------------
# Dataframe construction
# ---------------------------------------------------------------------


def build_quote_dataframe(snapshot) -> pd.DataFrame:
    columns = [
        "Type",
        "Strike",
        "Bid",
        "Ask",
        "Mid",
        "Spread",
        "Last",
        "Price Source",
        "Last Trade",
    ]

    rows: list[dict[str, Any]] = []

    for quote in snapshot.option_quotes:
        bid = safe_float(
            get_first_attribute(
                quote,
                ["bid"],
                0.0,
            )
        )

        ask = safe_float(
            get_first_attribute(
                quote,
                ["ask"],
                0.0,
            )
        )

        mid = safe_float(
            get_first_attribute(
                quote,
                ["mid_price", "market_price"],
            )
        )

        last = safe_float(
            get_first_attribute(
                quote,
                ["last_price"],
            )
        )

        bid = bid or 0.0
        ask = ask or 0.0

        has_live_market = bid > 0 and ask > 0

        rows.append(
            {
                "Type": normalise_option_type(quote.option.option_type),
                "Strike": safe_float(quote.option.strike),
                "Bid": bid,
                "Ask": ask,
                "Mid": mid,
                "Spread": (ask - bid if has_live_market else None),
                "Last": last,
                "Price Source": ("Midpoint" if has_live_market else "Last trade"),
                "Last Trade": get_first_attribute(
                    quote,
                    ["last_trade_time"],
                ),
            }
        )

    dataframe = pd.DataFrame(
        rows,
        columns=columns,
    )

    if dataframe.empty:
        return dataframe

    dataframe["Strike"] = pd.to_numeric(
        dataframe["Strike"],
        errors="coerce",
    )

    return dataframe.sort_values(
        by=["Type", "Strike"],
    ).reset_index(drop=True)


def build_analysis_dataframe(
    analysis,
) -> pd.DataFrame:
    columns = [
        "Type",
        "Strike",
        "Bid",
        "Ask",
        "Mid",
        "Spread",
        "IV",
        "Model Price",
        "Delta",
        "Gamma",
        "Vega",
        "Theta",
        "Rho",
    ]

    rows: list[dict[str, Any]] = []

    analysis_rows = get_first_attribute(
        analysis,
        ["rows"],
        [],
    )

    for row in analysis_rows:
        option = get_first_attribute(
            row,
            ["option"],
        )

        quote = get_first_attribute(
            row,
            ["quote", "option_quote"],
        )

        greeks = get_first_attribute(
            row,
            ["greeks"],
        )

        option_type = get_first_attribute(
            row,
            ["option_type"],
        )

        strike = get_first_attribute(
            row,
            ["strike"],
        )

        if option is not None:
            if option_type is None:
                option_type = get_first_attribute(
                    option,
                    ["option_type"],
                )

            if strike is None:
                strike = get_first_attribute(
                    option,
                    ["strike"],
                )

        bid = get_first_attribute(
            row,
            ["bid"],
        )

        ask = get_first_attribute(
            row,
            ["ask"],
        )

        mid = get_first_attribute(
            row,
            [
                "mid_price",
                "market_price",
                "price",
            ],
        )

        spread = get_first_attribute(
            row,
            ["spread"],
        )

        if quote is not None:
            if bid is None:
                bid = get_first_attribute(
                    quote,
                    ["bid"],
                )

            if ask is None:
                ask = get_first_attribute(
                    quote,
                    ["ask"],
                )

            if mid is None:
                mid = get_first_attribute(
                    quote,
                    [
                        "mid_price",
                        "market_price",
                        "price",
                    ],
                )

        bid_number = safe_float(bid)
        ask_number = safe_float(ask)

        if spread is None and bid_number is not None and ask_number is not None:
            spread = ask_number - bid_number

        delta = get_first_attribute(
            row,
            ["delta"],
        )

        gamma = get_first_attribute(
            row,
            ["gamma"],
        )

        vega = get_first_attribute(
            row,
            ["vega"],
        )

        theta = get_first_attribute(
            row,
            ["theta"],
        )

        rho = get_first_attribute(
            row,
            ["rho"],
        )

        if greeks is not None:
            if delta is None:
                delta = get_first_attribute(
                    greeks,
                    ["delta"],
                )

            if gamma is None:
                gamma = get_first_attribute(
                    greeks,
                    ["gamma"],
                )

            if vega is None:
                vega = get_first_attribute(
                    greeks,
                    ["vega"],
                )

            if theta is None:
                theta = get_first_attribute(
                    greeks,
                    ["theta"],
                )

            if rho is None:
                rho = get_first_attribute(
                    greeks,
                    ["rho"],
                )

        rows.append(
            {
                "Type": normalise_option_type(option_type),
                "Strike": strike,
                "Bid": bid,
                "Ask": ask,
                "Mid": mid,
                "Spread": spread,
                "IV": get_first_attribute(
                    row,
                    [
                        "implied_volatility",
                        "implied_vol",
                        "iv",
                    ],
                ),
                "Model Price": get_first_attribute(
                    row,
                    [
                        "theoretical_price",
                        "model_price",
                        "black_scholes_price",
                    ],
                ),
                "Delta": delta,
                "Gamma": gamma,
                "Vega": vega,
                "Theta": theta,
                "Rho": rho,
            }
        )

    dataframe = pd.DataFrame(
        rows,
        columns=columns,
    )

    numeric_columns = [
        "Strike",
        "Bid",
        "Ask",
        "Mid",
        "Spread",
        "IV",
        "Model Price",
        "Delta",
        "Gamma",
        "Vega",
        "Theta",
        "Rho",
    ]

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    if dataframe.empty:
        return dataframe

    dataframe = dataframe.dropna(
        subset=["Strike"],
    )

    return dataframe.sort_values(
        by=["Type", "Strike"],
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# Option-chain filtering
# ---------------------------------------------------------------------


def apply_chain_filters(
    dataframe: pd.DataFrame,
    option_type: str,
    minimum_strike: float,
    maximum_strike: float,
) -> pd.DataFrame:
    filtered = dataframe.copy()

    if option_type == "Calls":
        filtered = filtered[filtered["Type"] == "call"]

    elif option_type == "Puts":
        filtered = filtered[filtered["Type"] == "put"]

    filtered = filtered[
        filtered["Strike"].between(
            minimum_strike,
            maximum_strike,
        )
    ]

    return filtered.reset_index(drop=True)


# ---------------------------------------------------------------------
# IV smile
# ---------------------------------------------------------------------


def plot_iv_smile(
    dataframe: pd.DataFrame,
    spot: float,
) -> plt.Figure | None:
    required_columns = {
        "Type",
        "Strike",
        "IV",
    }

    if not required_columns.issubset(dataframe.columns):
        return None

    if spot <= 0:
        return None

    chart_data = dataframe[["Type", "Strike", "IV"]].copy()

    chart_data["Type"] = chart_data["Type"].astype(str).str.lower().str.strip()

    chart_data["Strike"] = pd.to_numeric(
        chart_data["Strike"],
        errors="coerce",
    )

    chart_data["IV"] = pd.to_numeric(
        chart_data["IV"],
        errors="coerce",
    )

    chart_data = chart_data.dropna(
        subset=[
            "Type",
            "Strike",
            "IV",
        ]
    )

    chart_data = chart_data[
        chart_data["Strike"].gt(0)
        & chart_data["IV"].between(
            0.01,
            3.00,
        )
    ].copy()

    if chart_data.empty:
        return None

    chart_data["Moneyness"] = chart_data["Strike"] / float(spot)

    chart_data = chart_data[
        chart_data["Moneyness"].between(
            0.75,
            1.25,
        )
    ].copy()

    if chart_data.empty:
        return None

    figure, axis = plt.subplots(figsize=(10, 5))

    plotted_anything = False

    for option_type in [
        "call",
        "put",
    ]:
        group = chart_data[chart_data["Type"] == option_type].copy()

        group = (
            group.groupby(
                "Moneyness",
                as_index=False,
            )["IV"]
            .median()
            .sort_values("Moneyness")
        )

        if group.empty:
            continue

        moneyness = group["Moneyness"].to_numpy(dtype=float)

        implied_volatility = group["IV"].to_numpy(dtype=float)

        axis.scatter(
            moneyness,
            implied_volatility * 100,
            s=24,
            alpha=0.55,
            label=(f"{option_type.title()} observations"),
        )

        # A quadratic fit needs at least three distinct points.
        if len(group) >= 3:
            coefficients = np.polyfit(
                moneyness,
                implied_volatility,
                deg=2,
            )

            fitted_moneyness = np.linspace(
                moneyness.min(),
                moneyness.max(),
                150,
            )

            fitted_iv = np.polyval(
                coefficients,
                fitted_moneyness,
            )

            fitted_iv = np.clip(
                fitted_iv,
                0.01,
                3.00,
            )

            axis.plot(
                fitted_moneyness,
                fitted_iv * 100,
                linewidth=2,
                label=(f"{option_type.title()} quadratic fit"),
            )

        plotted_anything = True

    if not plotted_anything:
        plt.close(figure)
        return None

    axis.axvline(
        1.0,
        linestyle="--",
        linewidth=1,
        label="At the money",
    )

    axis.set_title("Implied Volatility Smile")

    axis.set_xlabel("Moneyness — Strike / Spot")

    axis.set_ylabel("Implied Volatility (%)")

    axis.grid(alpha=0.25)

    axis.legend()

    figure.tight_layout()

    return figure


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

with st.sidebar:
    st.markdown("## Market controls")

    with st.form("market_form"):
        symbol_input = st.text_input(
            "Ticker",
            value=st.session_state.get(
                "selected_symbol",
                "AAPL",
            ),
            help=("Enter a US equity ticker such as AAPL or NVDA."),
        )

        risk_free_rate = st.number_input(
            "Risk-free rate",
            min_value=0.0,
            max_value=0.25,
            value=float(
                st.session_state.get(
                    "risk_free_rate",
                    0.04,
                )
            ),
            step=0.005,
            format="%.3f",
        )

        dividend_yield = st.number_input(
            "Dividend yield",
            min_value=0.0,
            max_value=0.25,
            value=float(
                st.session_state.get(
                    "dividend_yield",
                    0.0,
                )
            ),
            step=0.005,
            format="%.3f",
        )

        load_market = st.form_submit_button(
            "Load market",
            type="primary",
            width="stretch",
        )

    if load_market:
        symbol = symbol_input.strip().upper()

        if not symbol:
            st.error("Enter a ticker.")
        else:
            with st.spinner(f"Loading {symbol} expiries..."):
                try:
                    expiries = load_expiries(symbol)

                    if not expiries:
                        raise ValueError("No option expiries were returned.")

                    st.session_state["selected_symbol"] = symbol

                    st.session_state["risk_free_rate"] = risk_free_rate

                    st.session_state["dividend_yield"] = dividend_yield

                    st.session_state["expiries"] = expiries

                    st.session_state["selected_expiry"] = expiries[0]

                    st.session_state.pop(
                        "snapshot",
                        None,
                    )

                    st.session_state.pop(
                        "analysis",
                        None,
                    )

                    st.session_state.pop(
                        "surface_observations",
                        None,
                    )

                    st.session_state.pop(
                        "surface_symbol",
                        None,
                    )

                    st.success(f"Loaded {len(expiries)} expiries for {symbol}.")

                except Exception as error:
                    st.error(f"Could not load {symbol}: {error}")

    symbol = st.session_state.get("selected_symbol")

    expiries = st.session_state.get(
        "expiries",
        [],
    )

    if symbol and expiries:
        stored_expiry = st.session_state.get(
            "selected_expiry",
            expiries[0],
        )

        try:
            expiry_index = expiries.index(stored_expiry)
        except ValueError:
            expiry_index = 0

        selected_expiry = st.selectbox(
            "Expiry",
            options=expiries,
            index=expiry_index,
            format_func=lambda expiry: expiry.strftime("%d %b %Y"),
        )

        refresh_snapshot = st.button(
            "Load option chain",
            type="primary",
            width="stretch",
        )

        if refresh_snapshot:
            with st.spinner(f"Downloading {symbol} option chain..."):
                try:
                    snapshot = load_snapshot(
                        symbol=symbol,
                        expiry=selected_expiry,
                    )

                    market = create_market_state(
                        spot=snapshot.spot,
                        risk_free_rate=float(
                            st.session_state.get(
                                "risk_free_rate",
                                risk_free_rate,
                            )
                        ),
                        dividend_yield=float(
                            st.session_state.get(
                                "dividend_yield",
                                dividend_yield,
                            )
                        ),
                    )

                    analysis = analyse_option_chain(
                        symbol=snapshot.symbol,
                        expiry=selected_expiry,
                        quotes=snapshot.option_quotes,
                        market=market,
                    )

                    st.session_state["snapshot"] = snapshot

                    st.session_state["analysis"] = analysis

                    st.session_state["selected_expiry"] = selected_expiry

                except Exception as error:
                    st.error(f"Could not load option chain: {error}")

        if st.button(
            "Clear cached market data",
            width="stretch",
        ):
            st.cache_data.clear()

            for key in [
                "snapshot",
                "analysis",
                "surface_observations",
                "surface_symbol",
            ]:
                st.session_state.pop(
                    key,
                    None,
                )

            st.rerun()

# ---------------------------------------------------------------------
# Main header
# ---------------------------------------------------------------------

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">pyquant</div>
        <div class="app-subtitle">
            Options analytics, risk and volatility modelling
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

snapshot = st.session_state.get("snapshot")

analysis = st.session_state.get("analysis")

if snapshot is None or analysis is None:
    st.info(
        "Enter a ticker in the sidebar, click **Load market**, "
        "choose an expiry, and then click **Load option chain**."
    )

    st.markdown("### Dashboard modules")

    module_1, module_2, module_3 = st.columns(3)

    with module_1:
        st.markdown("#### Market snapshot")
        st.write("Spot data and option-chain quote quality.")

    with module_2:
        st.markdown("#### Options analytics")
        st.write("Implied volatility, Greeks and model prices.")

    with module_3:
        st.markdown("#### Volatility modelling")
        st.write("Smile and multi-expiry surface visualisation.")

    st.stop()

# ---------------------------------------------------------------------
# Prepare current data
# ---------------------------------------------------------------------

quote_dataframe = build_quote_dataframe(snapshot)

analysis_dataframe = build_analysis_dataframe(analysis)

if quote_dataframe.empty:
    live_quotes = quote_dataframe.copy()
    fallback_quotes = quote_dataframe.copy()
    calls = quote_dataframe.copy()
    puts = quote_dataframe.copy()
else:
    live_quotes = quote_dataframe[quote_dataframe["Price Source"] == "Midpoint"]

    fallback_quotes = quote_dataframe[quote_dataframe["Price Source"] == "Last trade"]

    calls = quote_dataframe[quote_dataframe["Type"] == "call"]

    puts = quote_dataframe[quote_dataframe["Type"] == "put"]

selected_expiry = st.session_state.get("selected_expiry")

# ---------------------------------------------------------------------
# Header metrics
# ---------------------------------------------------------------------

st.markdown(f"### {snapshot.symbol} · {selected_expiry:%d %B %Y}")

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

metric_1.metric(
    "Spot",
    f"${snapshot.spot:,.2f}",
)

metric_2.metric(
    "Contracts",
    f"{len(quote_dataframe):,}",
)

metric_3.metric(
    "Calls",
    f"{len(calls):,}",
)

metric_4.metric(
    "Puts",
    f"{len(puts):,}",
)

metric_5.metric(
    "Live bid / ask",
    f"{len(live_quotes):,}",
)

st.caption(f"Snapshot captured at {snapshot.timestamp}")

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------

(
    overview_tab,
    chain_tab,
    smile_tab,
    surface_tab,
    diagnostics_tab,
) = st.tabs(
    [
        "Overview",
        "Option chain",
        "IV smile",
        "Volatility surface",
        "Diagnostics",
    ]
)

# ---------------------------------------------------------------------
# Overview tab
# ---------------------------------------------------------------------

with overview_tab:
    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("At-the-money contracts")

        if analysis_dataframe.empty:
            st.warning("No options were successfully analysed.")

        elif analysis_dataframe["Strike"].dropna().empty:
            st.warning("The analysis did not produce valid strikes.")

        else:
            atm = analysis_dataframe.copy()

            atm["Distance"] = (atm["Strike"] - float(snapshot.spot)).abs()

            atm = (
                atm.sort_values("Distance")
                .groupby(
                    "Type",
                    as_index=False,
                )
                .first()
            )

            display_columns = [
                column
                for column in [
                    "Type",
                    "Strike",
                    "Mid",
                    "IV",
                    "Delta",
                    "Gamma",
                    "Vega",
                    "Theta",
                ]
                if column in atm.columns
            ]

            st.dataframe(
                atm[display_columns],
                hide_index=True,
                width="stretch",
                column_config={
                    "Strike": (st.column_config.NumberColumn(format="$%.2f")),
                    "Mid": (st.column_config.NumberColumn(format="$%.2f")),
                    "IV": (st.column_config.NumberColumn(format="%.4f")),
                    "Delta": (st.column_config.NumberColumn(format="%.4f")),
                    "Gamma": (st.column_config.NumberColumn(format="%.6f")),
                    "Vega": (st.column_config.NumberColumn(format="%.4f")),
                    "Theta": (st.column_config.NumberColumn(format="%.4f")),
                },
            )

    with right:
        st.subheader("Quote quality")

        quote_count = len(quote_dataframe)

        midpoint_percentage = (
            len(live_quotes) / quote_count * 100 if quote_count > 0 else 0
        )

        fallback_percentage = (
            len(fallback_quotes) / quote_count * 100 if quote_count > 0 else 0
        )

        st.metric(
            "Midpoint coverage",
            f"{midpoint_percentage:.1f}%",
        )

        st.metric(
            "Last-price fallback",
            f"{fallback_percentage:.1f}%",
        )

        if midpoint_percentage < 50:
            st.warning(
                "A large proportion of contracts use "
                "last-trade prices. IV estimates may be stale."
            )
        else:
            st.success("Most contracts have positive bid and ask quotes.")

# ---------------------------------------------------------------------
# Option-chain tab
# ---------------------------------------------------------------------

with chain_tab:
    st.subheader("Option chain")

    valid_strikes = analysis_dataframe["Strike"].dropna()

    if analysis_dataframe.empty:
        st.warning("No analysed option rows are available.")

    elif valid_strikes.empty:
        st.warning("No valid option strikes are available.")

    else:
        minimum_available_strike = float(valid_strikes.min())

        maximum_available_strike = float(valid_strikes.max())

        filter_1, filter_2 = st.columns([1, 2])

        with filter_1:
            option_type_filter = st.radio(
                "Option type",
                options=[
                    "All",
                    "Calls",
                    "Puts",
                ],
                horizontal=True,
            )

        with filter_2:
            if minimum_available_strike == maximum_available_strike:
                strike_range = (
                    minimum_available_strike,
                    maximum_available_strike,
                )

                st.caption(
                    f"Only one strike is available: {minimum_available_strike:.2f}"
                )

            else:
                strike_range = st.slider(
                    "Strike range",
                    min_value=minimum_available_strike,
                    max_value=maximum_available_strike,
                    value=(
                        minimum_available_strike,
                        maximum_available_strike,
                    ),
                )

        filtered_chain = apply_chain_filters(
            dataframe=analysis_dataframe,
            option_type=option_type_filter,
            minimum_strike=strike_range[0],
            maximum_strike=strike_range[1],
        )

        st.dataframe(
            filtered_chain,
            hide_index=True,
            width="stretch",
            height=600,
            column_config={
                "Strike": (st.column_config.NumberColumn(format="$%.2f")),
                "Bid": (st.column_config.NumberColumn(format="$%.2f")),
                "Ask": (st.column_config.NumberColumn(format="$%.2f")),
                "Mid": (st.column_config.NumberColumn(format="$%.2f")),
                "Spread": (st.column_config.NumberColumn(format="$%.2f")),
                "Model Price": (st.column_config.NumberColumn(format="$%.2f")),
                "IV": (st.column_config.NumberColumn(format="%.4f")),
                "Delta": (st.column_config.NumberColumn(format="%.4f")),
                "Gamma": (st.column_config.NumberColumn(format="%.6f")),
                "Vega": (st.column_config.NumberColumn(format="%.4f")),
                "Theta": (st.column_config.NumberColumn(format="%.4f")),
                "Rho": (st.column_config.NumberColumn(format="%.4f")),
            },
        )

        st.download_button(
            "Download chain as CSV",
            data=filtered_chain.to_csv(index=False),
            file_name=(f"{snapshot.symbol}_{selected_expiry}_option_chain.csv"),
            mime="text/csv",
        )

# ---------------------------------------------------------------------
# IV-smile tab
# ---------------------------------------------------------------------

with smile_tab:
    st.subheader("Implied Volatility Smile")

    smile_figure = plot_iv_smile(
        dataframe=analysis_dataframe,
        spot=float(snapshot.spot),
    )

    if smile_figure is None:
        st.warning(
            "There are not enough valid implied-volatility "
            "observations to plot the smile."
        )
    else:
        st.pyplot(
            smile_figure,
            width="stretch",
        )

        plt.close(smile_figure)

# ---------------------------------------------------------------------
# Volatility-surface tab
# ---------------------------------------------------------------------

with surface_tab:
    st.subheader("Implied Volatility Surface")

    target_days = [
        7,
        14,
        30,
        60,
        90,
        180,
        365,
    ]

    future_expiries = [expiry for expiry in expiries if expiry > date.today()]

    surface_expiries: list[date] = []

    for target_day in target_days:
        if not future_expiries:
            break

        target_expiry = date.today() + timedelta(days=target_day)

        closest_expiry = min(
            future_expiries,
            key=lambda expiry: abs((expiry - target_expiry).days),
        )

        if closest_expiry not in surface_expiries:
            surface_expiries.append(closest_expiry)

    if not surface_expiries:
        st.warning("No future expiries are available.")

    else:
        st.caption(
            "Expiries used: "
            + ", ".join(expiry.strftime("%d %b %Y") for expiry in surface_expiries)
        )

        if st.button(
            "Build volatility surface",
            type="primary",
            key="build_surface_button",
        ):
            analyses = []

            progress = st.progress(0)
            status = st.empty()

            total_expiries = len(surface_expiries)

            for index, expiry in enumerate(surface_expiries):
                status.write(f"Analysing {symbol} options for {expiry:%d %b %Y}...")

                try:
                    expiry_analysis = load_option_analysis(
                        symbol=symbol,
                        expiry=expiry,
                        risk_free_rate=(risk_free_rate),
                        dividend_yield=(dividend_yield),
                    )

                    analysis_rows = get_first_attribute(
                        expiry_analysis,
                        ["rows"],
                        [],
                    )

                    if not analysis_rows:
                        st.warning(
                            f"Skipped "
                            f"{expiry:%d %b %Y}: "
                            "no options were "
                            "successfully analysed."
                        )
                        continue

                    analyses.append(expiry_analysis)

                except Exception as error:
                    st.warning(f"Skipped {expiry:%d %b %Y}: {error}")

                finally:
                    progress.progress((index + 1) / total_expiries)

            status.empty()
            progress.empty()

            if len(analyses) < 2:
                st.error(
                    "At least two expiry analyses are needed to build the surface."
                )

            else:
                try:
                    surface = build_volatility_surface(
                        analyses=analyses,
                        degree=2,
                    )

                    st.session_state["volatility_surface"] = surface

                except Exception as error:
                    st.error(f"Could not build volatility surface: {error}")

        surface = st.session_state.get("volatility_surface")

        if surface is not None:
            try:
                surface_figure = plot_volatility_surface(
                    surface,
                    minimum_moneyness=0.90,
                    maximum_moneyness=1.10,
                    number_of_strikes=100,
                )

                st.pyplot(
                    surface_figure,
                    width="stretch",
                )

                plt.close(surface_figure)

                st.success(f"Built a surface from {len(surface.smiles)} expiries.")

            except Exception as error:
                st.error(f"Could not plot volatility surface: {error}")

# ---------------------------------------------------------------------
# Diagnostics tab
# ---------------------------------------------------------------------

with diagnostics_tab:
    st.subheader("Market-data diagnostics")

    diagnostic_1, diagnostic_2, diagnostic_3 = st.columns(3)

    diagnostic_1.metric(
        "Positive bid and ask",
        len(live_quotes),
    )

    diagnostic_2.metric(
        "Last-price fallback",
        len(fallback_quotes),
    )

    diagnostic_3.metric(
        "Successfully analysed",
        len(analysis_dataframe),
    )

    st.markdown("#### Raw downloaded quotes")

    st.dataframe(
        quote_dataframe,
        hide_index=True,
        width="stretch",
        height=500,
    )

    with st.expander("Application state"):
        st.write(
            {
                "symbol": snapshot.symbol,
                "expiry": selected_expiry,
                "spot": snapshot.spot,
                "snapshot_time": (snapshot.timestamp),
                "downloaded_quotes": len(snapshot.option_quotes),
                "analysed_quotes": len(analysis_dataframe),
                "analysis_columns": (analysis_dataframe.columns.tolist()),
            }
        )

        analysis_rows = get_first_attribute(
            analysis,
            ["rows"],
            [],
        )

        if analysis_rows:
            first_row = analysis_rows[0]

            try:
                st.write(
                    "First raw analysis row:",
                    vars(first_row),
                )
            except TypeError:
                st.write(
                    "First raw analysis row:",
                    first_row,
                )
