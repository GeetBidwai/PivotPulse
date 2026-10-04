"""Streamlit dashboard for scanning NSE VCP signals."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

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

    prepared["date"] = pd.to_datetime(
        prepared["date"],
    )

    prepared["score"] = pd.to_numeric(
        prepared["score"],
        errors="coerce",
    )

    return (
        prepared
        .sort_values(
            ["date", "score"],
            ascending=[False, False],
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
        )
        .drop_duplicates(
            subset=["symbol"],
            keep="first",
        )
        .reset_index(drop=True)
    )


if "scan_results" not in st.session_state:
    st.session_state.scan_results = empty_results()

if "scan_completed" not in st.session_state:
    st.session_state.scan_completed = False


st.title("PivotPulse")
st.caption("NSE VCP Scanner")

st.write(
    "Find historical VCP setups and potential breakouts "
    "across selected NSE stocks."
)


with st.sidebar:
    st.header("Scan settings")

    symbols = st.multiselect(
        "Stocks to scan",
        options=DEFAULT_SYMBOLS,
        default=DEFAULT_SYMBOLS,
        help="Choose one or more symbols from the current MVP watchlist.",
    )

    date_range = st.date_input(
        "Date range",
        value=(
            date.today() - timedelta(days=365),
            date.today(),
        ),
        max_value=date.today(),
        help=(
            "Shows signals from this period. "
            "PivotPulse automatically fetches earlier history "
            "for indicator calculations."
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


st.subheader("Results")


filter_left, filter_middle, filter_right = st.columns(3)


with filter_left:
    selected_stocks = st.multiselect(
        "Filter by stock",
        options=sorted(
            results["symbol"].unique()
        ),
        default=None,
    )


with filter_middle:
    selected_signals = st.multiselect(
        "Filter by signal type",
        options=sorted(
            results["signal"].unique()
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
    )
)


latest_results = latest_signal_per_stock(
    filtered_results,
)


total_signals = len(latest_results)

setups = latest_results["signal"].eq(
    "setup"
).sum()

breakouts = latest_results["signal"].eq(
    "breakout"
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


display_results = latest_results[
    [
        "symbol",
        "date",
        "score",
        "classification",
        "signal",
        "trend_qualified",
        "in_base",
        "breakout",
    ]
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