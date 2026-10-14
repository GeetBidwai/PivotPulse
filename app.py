"""Streamlit dashboard for PivotPulse."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st


import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data.nse_instruments import load_nse_equity_instruments
from src.data.providers.upstox_provider import UpstoxMarketDataProvider

from src.data.upstox_auth import get_upstox_access_token
from src.multi_stock_scanner import (
    OUTPUT_COLUMNS,
    filter_signals_to_display_range,
    scan_stocks,
)


DEFAULT_SYMBOLS = [
    "RELIANCE",
    "INFY",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "JNPR",
]


st.set_page_config(
    page_title="PivotPulse",
    page_icon="📈",
    layout="wide",
)


def empty_results() -> pd.DataFrame:
    """Create the expected empty result shape."""

    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def normalise_results(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare scanner results for display."""

    prepared = results.copy()

    if prepared.empty:
        return prepared

    prepared["date"] = pd.to_datetime(
        prepared["date"],
    )

    prepared["score"] = pd.to_numeric(
        prepared["score"],
        errors="coerce",
    )

    numeric_columns = [
        "current_price",
        "pivot",
        "support",
        "atr_percent",
    ]

    for column in numeric_columns:
        if column in prepared.columns:
            prepared[column] = pd.to_numeric(
                prepared[column],
                errors="coerce",
            )

    return (
        prepared
        .sort_values(
            ["date", "score"],
            ascending=[False, False],
            na_position="last",
        )
        .reset_index(drop=True)
    )


def latest_signal_per_stock(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Keep only the latest signal for each stock."""

    if results.empty:
        return results.copy()

    return (
        results
        .sort_values(
            ["date", "score"],
            ascending=[False, False],
            na_position="last",
        )
        .drop_duplicates(
            subset=["symbol"],
            keep="first",
        )
        .reset_index(drop=True)
    )


def show_jnpr_price_chart(start_date, end_date):
    """Display JNPR daily candles, pivot, support and volume."""

    instruments = load_nse_equity_instruments()
    matches = instruments[
        instruments["trading_symbol"].eq("JNPR")
    ]

    if matches.empty:
        st.warning("JNPR instrument was not found.")
        return

    instrument_key = matches.iloc[0]["instrument_key"]
    provider = UpstoxMarketDataProvider()

    try:
        df = provider.get_daily_data(
            symbol=instrument_key,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as error:
        st.warning(f"Unable to load JNPR chart data: {error}")
        return

    if df.empty:
        st.info("No JNPR price data is available for this period.")
        return

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    for column in ["Open", "High", "Low", "Close", "Volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["Date", "Open", "High", "Low", "Close", "Volume"]
    )

    if df.empty:
        st.info("No valid candles are available for JNPR.")
        return

    # Match the levels shown by the current early-VCP model.
    pivot = float(df["High"].iloc[-21:-1].max())
    support = float(df["Low"].tail(20).min())

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
    )

    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="JNPR",
        ),
        row=1,
        col=1,
    )

    fig.add_hline(
        y=pivot,
        line_dash="dash",
        annotation_text=f"Pivot ₹{pivot:.2f}",
        row=1,
        col=1,
    )

    fig.add_hline(
        y=support,
        line_dash="dot",
        annotation_text=f"Support ₹{support:.2f}",
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="JNPR — Daily Price and Volume",
        height=650,
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, width="stretch")


if "scan_results" not in st.session_state:
    st.session_state.scan_results = empty_results()

if "scan_completed" not in st.session_state:
    st.session_state.scan_completed = False


st.title("PivotPulse")
st.caption("NSE VCP Scanner")

st.write(
    "Find VCP setups and potential breakouts across selected NSE stocks."
)


with st.sidebar:
    st.header("Scan settings")

    symbols = st.multiselect(
        "Stocks to scan",
        options=DEFAULT_SYMBOLS,
        default=DEFAULT_SYMBOLS,
        help="Choose one or more NSE stocks.",
    )

    date_range = st.date_input(
        "Date range",
        value=(
            date.today() - timedelta(days=365),
            date.today(),
        ),
        max_value=date.today(),
        help=(
            "Select the period in which you want to see signals. "
            "PivotPulse automatically fetches earlier history when needed."
        ),
    )

    scan_requested = st.button(
        "Scan VCP signals",
        type="primary",
        width="stretch",
    )


if scan_requested:
    if not symbols:
        st.warning(
            "Select at least one stock before scanning."
        )

    elif (
        not isinstance(date_range, tuple)
        or len(date_range) != 2
    ):
        st.warning(
            "Select both a start and end date."
        )

    else:
        start_date, end_date = date_range

        if start_date > end_date:
            st.warning(
                "The start date must be on or before the end date."
            )

        else:
            try:
                get_upstox_access_token()

                with st.spinner(
                    "Scanning market data…"
                ):
                    scan_results = scan_stocks(
                        symbols=symbols,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    scan_results = (
                        filter_signals_to_display_range(
                            scan_results,
                            start_date,
                            end_date,
                        )
                    )

                    st.session_state.scan_results = (
                        normalise_results(
                            scan_results,
                        )
                    )

                st.session_state.scan_completed = True

            except RuntimeError as error:
                st.error(
                    f"Unable to scan market data: {error}"
                )

            except Exception as error:
                st.error(
                    "The market-data request could not be "
                    "completed. Please check your Upstox "
                    f"connection and try again.\n\n{error}"
                )


results = st.session_state.scan_results


if results.empty:
    if st.session_state.scan_completed:
        st.info(
            "No VCP signals were found for the selected "
            "stocks and date range."
        )
    else:
        st.info(
            "Choose stocks and a date range, then run a "
            "scan. Matching VCP signals will appear here."
        )

    st.stop()


st.subheader("Signals")


filter_left, filter_middle, filter_right = st.columns(3)


with filter_left:
    selected_stocks = st.multiselect(
        "Filter by stock",
        options=sorted(
            results["symbol"].dropna().unique()
        ),
        default=None,
    )


with filter_middle:
    selected_signals = st.multiselect(
        "Filter by signal type",
        options=sorted(
            results["signal"].dropna().unique()
        ),
        default=None,
    )


with filter_right:
    minimum_score = st.slider(
        "Minimum VCP score",
        0,
        100,
        0,
        1,
    )


filtered_results = results.loc[
    results["score"].ge(minimum_score)
].copy()


if selected_stocks:
    filtered_results = filtered_results.loc[
        filtered_results["symbol"].isin(
            selected_stocks
        )
    ]


if selected_signals:
    filtered_results = filtered_results.loc[
        filtered_results["signal"].isin(
            selected_signals
        )
    ]


filtered_results = (
    filtered_results
    .sort_values(
        ["date", "score"],
        ascending=[False, False],
        na_position="last",
    )
)


latest_results = latest_signal_per_stock(
    filtered_results,
)


total_signals = len(latest_results)

setups = latest_results["signal"].eq(
    "SETUP"
).sum()

breakouts = latest_results["signal"].eq(
    "BREAKOUT"
).sum()


metric_one, metric_two, metric_three = st.columns(3)

metric_one.metric(
    "Stocks with signals",
    total_signals,
)

metric_two.metric(
    "Setups",
    setups,
)

metric_three.metric(
    "Breakouts",
    breakouts,
)


if latest_results.empty:
    st.info(
        "No signals match the selected filters. "
        "Try lowering the minimum score or clearing a filter."
    )

    st.stop()


# ------------------------------------------------------------
# Client-facing signal panel
# ------------------------------------------------------------

for _, signal_row in latest_results.iterrows():
    symbol = signal_row["symbol"]
    signal = str(signal_row["signal"]).upper()
    classification = str(
        signal_row["classification"]
    ).replace("_", " ").title()

    score = signal_row["score"]

    current_price = signal_row.get(
        "current_price",
        pd.NA,
    )

    pivot = signal_row.get(
        "pivot",
        pd.NA,
    )

    support = signal_row.get(
        "support",
        pd.NA,
    )

    atr_percent = signal_row.get(
        "atr_percent",
        pd.NA,
    )

    reason = signal_row.get(
        "reason",
        pd.NA,
    )

    st.divider()

    st.subheader(
        f"{symbol} — {classification.upper()} {signal}"
    )

    if signal == "BREAKOUT":
        st.success(
            "BREAKOUT CONFIRMED"
        )

    elif signal == "SETUP":
        st.info(
            "EARLY VCP SETUP — BREAKOUT NOT CONFIRMED"
        )

    else:
        st.warning(
            f"{signal}"
        )

    price_col, score_col, pivot_col, support_col = (
        st.columns(4)
    )

    with price_col:
        if pd.notna(current_price):
            st.metric(
                "Current Price",
                f"₹{float(current_price):,.2f}",
            )
        else:
            st.metric(
                "Current Price",
                "—",
            )

    with score_col:
        if pd.notna(score):
            st.metric(
                "VCP Score",
                f"{float(score):.0f}/100",
            )
        else:
            st.metric(
                "VCP Score",
                "—",
            )

    with pivot_col:
        if pd.notna(pivot):
            st.metric(
                "Pivot",
                f"₹{float(pivot):,.2f}",
            )
        else:
            st.metric(
                "Pivot",
                "—",
            )

    with support_col:
        if pd.notna(support):
            st.metric(
                "Support",
                f"₹{float(support):,.2f}",
            )
        else:
            st.metric(
                "Support",
                "—",
            )

    detail_left, detail_middle, detail_right = (
        st.columns(3)
    )

    with detail_left:
        st.write(
            f"**Classification:** {classification}"
        )

        trend_status = (
            "Positive"
            if bool(
                signal_row["trend_qualified"]
            )
            else "Not confirmed"
        )

        st.write(
            f"**Trend:** {trend_status}"
        )

    with detail_middle:
        if pd.notna(atr_percent):
            st.write(
                f"**ATR:** {float(atr_percent):.2f}%"
            )

        price_contracting = signal_row.get(
            "price_contracting",
            pd.NA,
        )

        if pd.notna(price_contracting):
            st.write(
                "**Price contraction:** "
                + (
                    "Yes"
                    if bool(price_contracting)
                    else "No"
                )
            )

    with detail_right:
        volume_contracting = signal_row.get(
            "volume_contracting",
            pd.NA,
        )

        if pd.notna(volume_contracting):
            st.write(
                "**Volume contraction:** "
                + (
                    "Yes"
                    if bool(volume_contracting)
                    else "No"
                )
            )

        breakout = bool(
            signal_row["breakout"]
        )

        st.write(
            "**Breakout:** "
            + (
                "Confirmed"
                if breakout
                else "Not confirmed"
            )
        )


    if pd.notna(reason):
        st.write(f"**Signal rationale:** {reason}")

    # Early VCP diagnostics
    pullbacks = signal_row.get("pullbacks_percent", pd.NA)

    if classification.lower() == "Early Vcp".lower():
        if isinstance(pullbacks, (list, tuple)) and pullbacks:
            formatted_pullbacks = " → ".join(
                f"{float(value):.2f}%" for value in pullbacks
            )
            st.write(f"**Recent measured pullbacks:** {formatted_pullbacks}")
        else:
            st.write("**Recent measured pullbacks:** Not available")

        if pd.notna(current_price) and pd.notna(pivot) and float(pivot) > 0:
            distance_pct = (
                (float(pivot) - float(current_price)) / float(pivot)
            ) * 100
            if distance_pct >= 0:
                st.write(f"**Distance below pivot:** {distance_pct:.2f}%")
            else:
                st.write(f"**Above pivot:** {abs(distance_pct):.2f}%")

# End of the signal-card loop

st.divider()
st.subheader("JNPR Price Chart")

if isinstance(date_range, tuple) and len(date_range) == 2:
    chart_start = date_range[0] - timedelta(days=400)
    chart_end = date_range[1]

    show_jnpr_price_chart(chart_start, chart_end)

# ------------------------------------------------------------
# Detailed results table
# ------------------------------------------------------------

st.divider()

st.subheader("Signal History")


display_columns = [
    "symbol",
    "date",
    "score",
    "classification",
    "signal",
    "status",
    "trend_qualified",
    "in_base",
    "breakout",
]


display_results = latest_results[
    display_columns
].copy()


display_results["date"] = (
    display_results["date"].dt.date
)

display_results["score"] = (
    display_results["score"]
    .round(0)
    .astype("Int64")
)


st.dataframe(
    display_results,
    column_config={
        "symbol": st.column_config.TextColumn(
            "Stock"
        ),
        "date": st.column_config.DateColumn(
            "Date",
            format="DD MMM YYYY",
        ),
        "score": st.column_config.NumberColumn(
            "VCP score",
            format="%d",
        ),
        "classification": st.column_config.TextColumn(
            "Classification"
        ),
        "signal": st.column_config.TextColumn(
            "Signal"
        ),
        "status": st.column_config.TextColumn(
            "Status"
        ),
        "trend_qualified": st.column_config.CheckboxColumn(
            "Trend qualified"
        ),
        "in_base": st.column_config.CheckboxColumn(
            "In base"
        ),
        "breakout": st.column_config.CheckboxColumn(
            "Breakout"
        ),
    },
    hide_index=True,
    width="stretch",
)