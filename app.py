"""Streamlit dashboard for PivotPulse."""

from datetime import date, datetime, timedelta
from base64 import b64encode
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.data.nse_instruments import load_nse_equity_instruments
from src.data.providers.upstox_provider import UpstoxMarketDataProvider
from src.data.upstox_auth import get_upstox_access_token
from src.multi_stock_scanner import OUTPUT_COLUMNS, filter_signals_to_display_range, scan_stocks


DEFAULT_SYMBOLS = ["RELIANCE", "INFY", "TCS", "HDFCBANK", "ICICIBANK", "JNPR"]
SPLASH_ARTWORK = Path(__file__).parent / "assets" / "loki-splash.png"
st.set_page_config(page_title="PivotPulse", page_icon="📈", layout="wide")


def apply_theme() -> None:
    """Apply a small, presentation-only light theme."""
    st.markdown("""<style>
    .stApp {background:#f6f8fb;color:#10233f}
    .pp-eyebrow{color:#245fae;font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.pp-title{color:#10233f;font-size:2.15rem;font-weight:750;margin:.05rem 0}.pp-subtitle,.pp-muted{color:#526a8d}.pp-subtitle{margin-bottom:.75rem}.pp-card{background:#fff;border:1px solid #d9e2ef;border-radius:14px;padding:1rem;box-shadow:0 2px 8px rgba(16,35,63,.04)}.pp-card h3{color:#10233f;margin:0 0 .25rem;font-size:1.08rem}.pp-muted{font-size:.9rem}.pp-badge{display:inline-block;border-radius:999px;padding:.25rem .6rem;font-size:.75rem;font-weight:700}.pp-setup{background:#fff1d6;color:#925500}.pp-breakout{background:#e2f5ea;color:#12683d}.pp-neutral{background:#e9eff7;color:#334e72}.pp-value{color:#10233f;font-size:1.35rem;font-weight:700;margin:.55rem 0}.pp-note{background:#fff;border:1px dashed #aebed2;border-radius:10px;color:#405b80;padding:.8rem 1rem}.st-key-mobile_history{display:none}div[data-testid="stMetric"]{background:#fff;border:1px solid #d9e2ef;border-radius:12px;padding:.7rem .8rem}div[data-testid="stMetricLabel"]{color:#405b80}div[data-testid="stMetricValue"]{color:#10233f}button[kind="primary"]{min-height:48px;font-weight:700}
    @media (max-width: 640px){.block-container{padding:1rem .85rem 2rem}.pp-title{font-size:1.7rem}.pp-card{padding:.9rem}.st-key-mobile_history{display:block}.st-key-desktop_history{display:none}div[data-testid="stMetric"]{padding:.6rem .7rem}}
    .pp-splash{align-items:center;background:#e5f0dd;display:flex;inset:0;justify-content:center;position:fixed;z-index:999999;animation:pp-splash-exit .4s ease 2.3s forwards}.pp-splash img{display:block;max-height:76vh;max-width:78vw;object-fit:contain;animation:pp-splash-enter .55s ease-out both}@keyframes pp-splash-enter{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:scale(1)}}@keyframes pp-splash-exit{to{opacity:0;visibility:hidden}}
    </style>""", unsafe_allow_html=True)


def render_splash() -> None:
    """Show the supplied artwork once without delaying app initialization."""
    if st.session_state.get("splash_shown") or not SPLASH_ARTWORK.is_file():
        return

    artwork = b64encode(SPLASH_ARTWORK.read_bytes()).decode("ascii")
    st.markdown(
        f"<div class='pp-splash'><img src='data:image/jpeg;base64,{artwork}' "
        "alt=''></div>",
        unsafe_allow_html=True,
    )
    st.session_state.splash_shown = True


def empty_results() -> pd.DataFrame:
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def normalise_results(results: pd.DataFrame) -> pd.DataFrame:
    """Prepare the scanner's existing result contract for display."""
    prepared = results.copy()
    if prepared.empty:
        return prepared
    prepared["date"] = pd.to_datetime(prepared["date"])
    prepared["score"] = pd.to_numeric(prepared["score"], errors="coerce")
    for column in ["current_price", "pivot", "support", "atr_percent"]:
        if column in prepared:
            prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared.sort_values(["date", "score"], ascending=[False, False], na_position="last").reset_index(drop=True)


def latest_signal_per_stock(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results.copy()
    return results.sort_values(["date", "score"], ascending=[False, False], na_position="last").drop_duplicates("symbol", keep="first").reset_index(drop=True)


def money(value) -> str:
    return f"₹{float(value):,.2f}" if pd.notna(value) else "—"


def display_date(value) -> str:
    return pd.Timestamp(value).strftime("%d %b %Y") if pd.notna(value) else "Not available"


def is_true(value) -> bool:
    """Treat unavailable scanner fields as unconfirmed in presentation."""
    return bool(value) if pd.notna(value) else False


@st.cache_data(show_spinner=False, ttl=3600)
def company_names() -> dict[str, str]:
    """Use the existing NSE instrument feed only for optional display labels."""
    try:
        instruments = load_nse_equity_instruments()
    except Exception:
        return {}
    return dict(zip(instruments["trading_symbol"], instruments["name"]))


@st.cache_data(show_spinner=False, ttl=3600)
def available_nse_stocks() -> pd.DataFrame:
    """Return searchable NSE equity symbols and company names."""
    instruments = load_nse_equity_instruments()

    stocks = instruments[["trading_symbol", "name"]].copy()
    stocks = stocks.dropna(subset=["trading_symbol"])
    stocks["trading_symbol"] = stocks["trading_symbol"].astype(str).str.strip()
    stocks["name"] = stocks["name"].fillna("").astype(str)

    stocks = stocks[stocks["trading_symbol"] != ""]
    stocks = stocks.drop_duplicates(
        subset=["trading_symbol"],
        keep="first",
    )

    return stocks.sort_values("trading_symbol").reset_index(drop=True)



def signal_badge(signal: str) -> tuple[str, str]:
    signal = str(signal).upper()
    if signal == "BREAKOUT":
        return "pp-breakout", "Breakout confirmed"
    if signal == "SETUP":
        return "pp-setup", "Developing setup"
    return "pp-neutral", signal.title()


def show_price_chart(symbol: str, start_date: date, end_date: date, pivot, support) -> None:
    """Render an actual provider-backed chart for the selected signal."""
    try:
        instruments = load_nse_equity_instruments()
        matches = instruments[instruments["trading_symbol"].eq(symbol)]
        if matches.empty:
            st.info("No NSE instrument mapping is available for this chart.")
            return
        data = UpstoxMarketDataProvider().get_daily_data(symbol=matches.iloc[0]["instrument_key"], start_date=start_date, end_date=end_date)
    except Exception as error:
        st.info(f"Price chart is unavailable: {error}")
        return
    if data.empty:
        st.info("No historical price data is available for this period.")
        return
    data = data.copy()
    data["Date"] = pd.to_datetime(data["Date"])
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.76, 0.24])
    figure.add_trace(go.Candlestick(x=data["Date"], open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"], name=symbol), row=1, col=1)
    if pd.notna(pivot):
        figure.add_hline(y=float(pivot), line_dash="dash", line_color="#3b82f6", annotation_text=f"Pivot {money(pivot)}", row=1, col=1)
    if pd.notna(support):
        figure.add_hline(y=float(support), line_dash="dot", line_color="#f59e0b", annotation_text=f"Support {money(support)}", row=1, col=1)
    figure.add_trace(go.Bar(x=data["Date"], y=data["Volume"], marker_color="#93c5fd", name="Volume"), row=2, col=1)
    figure.update_layout(height=550, margin=dict(l=12, r=12, t=35, b=12), xaxis_rangeslider_visible=False, legend_orientation="h", paper_bgcolor="#fff", plot_bgcolor="#fff")
    figure.update_yaxes(title_text="Price (₹)", row=1, col=1)
    figure.update_yaxes(title_text="Volume", row=2, col=1)
    st.plotly_chart(figure, width="stretch")


def render_card(row: pd.Series, name: str) -> None:
    badge_class, badge_text = signal_badge(row["signal"])
    classification = str(row.get("classification", "")).replace("_", " ").title()
    st.markdown(f"""<div class="pp-card"><span class="pp-badge {badge_class}">{badge_text}</span><h3>{row["symbol"]}</h3><div class="pp-muted">{name or "NSE equity"} · NSE</div><div class="pp-value">{money(row.get("current_price", pd.NA))}</div><div class="pp-muted">{classification} · Score {float(row["score"]):.0f}/100</div><div class="pp-muted">Pivot {money(row.get("pivot", pd.NA))} · Updated {display_date(row.get("date"))}</div></div>""", unsafe_allow_html=True)


def render_detail(row: pd.Series, all_results: pd.DataFrame, date_range) -> None:
    symbol = row["symbol"]
    name = company_names().get(symbol, "")
    if st.button("← Back to signal dashboard", key="back_to_dashboard"):
        st.session_state.selected_symbol = None
        st.rerun()
    st.markdown(f"<div class='pp-eyebrow'>NSE · VCP analysis</div><div class='pp-title'>{symbol}</div><div class='pp-subtitle'>{name or 'Company name unavailable'} · Latest scanner result: {display_date(row.get('date'))}</div>", unsafe_allow_html=True)
    badge_class, badge_text = signal_badge(row["signal"])
    st.markdown(f"<span class='pp-badge {badge_class}'>{badge_text}</span>", unsafe_allow_html=True)
    overview_top = st.columns(2)
    overview_top[0].metric("Latest available price", money(row.get("current_price", pd.NA)))
    overview_top[1].metric("VCP score", f"{float(row['score']):.0f}/100" if pd.notna(row.get("score")) else "—")
    overview_bottom = st.columns(2)
    overview_bottom[0].metric("Pivot price", money(row.get("pivot", pd.NA)))
    overview_bottom[1].metric("Support", money(row.get("support", pd.NA)))
    st.subheader("Price action")
    chart_end = date_range[1] if isinstance(date_range, tuple) and len(date_range) == 2 else date.today()
    show_price_chart(symbol, chart_end - timedelta(days=400), chart_end, row.get("pivot", pd.NA), row.get("support", pd.NA))
    st.subheader("VCP analysis")
    analysis_top = st.columns(2)
    analysis_top[0].metric("ATR", f"{float(row['atr_percent']):.2f}%" if pd.notna(row.get("atr_percent")) else "Not available")
    analysis_top[1].metric("Price contraction", "Confirmed" if is_true(row.get("price_contracting", False)) else "Not confirmed")
    st.metric("Volume contraction", "Confirmed" if is_true(row.get("volume_contracting", False)) else "Not confirmed")
    st.caption("SMA and relative-volume values are not included in the scanner result contract, so they are not shown here.")
    st.subheader("Pattern thesis")
    rationale = str(row.get("reason", "")) if pd.notna(row.get("reason", pd.NA)) else "The scanner returned this signal with the status shown above."
    st.write(f"**What the scanner detected:** {rationale}")
    conditions = ["Trend qualified" if is_true(row.get("trend_qualified", False)) else "Trend qualification not confirmed", "Base identified" if is_true(row.get("in_base", False)) else "Base not confirmed", "Breakout confirmed" if is_true(row.get("breakout", False)) else "Breakout not confirmed"]
    st.write("**Current conditions:** " + " · ".join(conditions))
    if str(row["signal"]).upper() == "SETUP":
        st.warning("This is a developing setup. The scanner has not confirmed a breakout.")
    elif str(row["signal"]).upper() == "BREAKOUT":
        st.success("The scanner marked this result as a confirmed breakout; this is a scanner status, not a recommendation.")
    st.subheader("Signal history")
    history = all_results[all_results["symbol"].eq(symbol)].copy()
    if history.empty:
        st.info("No stored signal history is available.")
    else:
        st.dataframe(history[["date", "score", "classification", "signal", "status"]], hide_index=True, width="stretch", column_config={"date": st.column_config.DateColumn("Date", format="DD MMM YYYY"), "score": st.column_config.NumberColumn("VCP score", format="%.0f")})


apply_theme()
if "scan_results" not in st.session_state:
    st.session_state.scan_results = empty_results()
if "scan_completed" not in st.session_state:
    st.session_state.scan_completed = False
if "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = None
if "selected_symbols" not in st.session_state:
    st.session_state.selected_symbols = DEFAULT_SYMBOLS
if "scan_date_range" not in st.session_state:
    st.session_state.scan_date_range = (date.today() - timedelta(days=365), date.today())

render_splash()

st.markdown("<div class='pp-eyebrow'>Market intelligence</div><div class='pp-title'>PivotPulse</div><div class='pp-subtitle'>Rule-based NSE VCP scanning for setups and confirmed breakouts.</div>", unsafe_allow_html=True)
with st.expander("Scan settings", expanded=True):
    
    stock_catalog = available_nse_stocks()

    stock_names = dict(
        zip(stock_catalog["trading_symbol"], stock_catalog["name"])
    )

    symbols = st.multiselect(
        "Search and select NSE stocks",
        options=stock_catalog["trading_symbol"].tolist(),
        key="selected_symbols",
        format_func=lambda symbol: (
            f"{symbol} — {stock_names.get(symbol, '')}"
            if stock_names.get(symbol)
            else symbol
        ),
        help="Type a stock symbol or company name. Select multiple stocks.",
    )

    date_col1, date_col2 = st.columns(2)

    with date_col1:
        start_date_text = st.text_input(
            "Start date (DD/MM/YYYY)",
            value=st.session_state.get(
                "manual_start_date",
                (date.today() - timedelta(days=365)).strftime("%d/%m/%Y"),
            ),
            key="manual_start_date",
            placeholder="20/01/2026",
        )

    with date_col2:
        end_date_text = st.text_input(
            "End date (DD/MM/YYYY)",
            value=st.session_state.get(
                "manual_end_date",
                date.today().strftime("%d/%m/%Y"),
            ),
            key="manual_end_date",
            placeholder="20/09/2026",
        )

    date_range = None
    date_error = None

    try:
        start_date = datetime.strptime(
            start_date_text.strip(), "%d/%m/%Y"
        ).date()
        end_date = datetime.strptime(
            end_date_text.strip(), "%d/%m/%Y"
        ).date()

        if start_date > end_date:
            date_error = "Start date must be on or before end date."
        elif end_date > date.today():
            date_error = "End date cannot be in the future."
        else:
            date_range = (start_date, end_date)

    except ValueError:
        date_error = "Enter valid dates in DD/MM/YYYY format."

scan_requested = st.button("Run VCP Scan", type="primary", width="stretch")

if scan_requested:
    if not symbols:
        st.warning("Select at least one stock before scanning.")
    elif date_error:
        st.warning(date_error)
    elif date_range is None:
        st.warning("Enter valid start and end dates.")
    else:
        try:
            get_upstox_access_token()
            with st.spinner("Scanning market data…"):
                scanned = scan_stocks(symbols=symbols, start_date=date_range[0], end_date=date_range[1])
                st.session_state.scan_results = normalise_results(filter_signals_to_display_range(scanned, date_range[0], date_range[1]))
            st.session_state.scan_completed = True
            st.session_state.selected_symbol = None
        except RuntimeError as error:
            st.error(f"Unable to scan market data: {error}")
        except Exception as error:
            st.error(f"The market-data request could not be completed. Please check your Upstox connection and try again.\n\n{error}")

results = st.session_state.scan_results
if st.session_state.selected_symbol and not results.empty:
    selected = results[results["symbol"].eq(st.session_state.selected_symbol)]
    if not selected.empty:
        render_detail(selected.iloc[0], results, date_range)
        st.stop()
    st.session_state.selected_symbol = None

if results.empty:
    message = "No VCP signals were found for the selected stocks and date range." if st.session_state.scan_completed else "Choose stocks and a date range above, then run a scan. Matching VCP signals will appear here."
    st.subheader("VCP signals")
    st.info(message)
    st.subheader("Market movers")
    st.markdown("<div class='pp-note'>Market-wide gainers and period returns are not available from the current scanner result contract.</div>", unsafe_allow_html=True)
    st.stop()

st.subheader("VCP signals")
with st.expander("Filter signal results"):
    selected_stocks = st.multiselect("Filter by stock", options=sorted(results["symbol"].dropna().unique()), key="result_stock_filter")
    selected_signals = st.multiselect("Filter by signal type", options=sorted(results["signal"].dropna().unique()), key="result_signal_filter")
    minimum_score = st.slider("Minimum VCP score", 0, 100, 0, 1, key="minimum_vcp_score")
filtered = results.loc[results["score"].ge(minimum_score)].copy()
if selected_stocks:
    filtered = filtered[filtered["symbol"].isin(selected_stocks)]
if selected_signals:
    filtered = filtered[filtered["signal"].isin(selected_signals)]
latest = latest_signal_per_stock(filtered.sort_values(["date", "score"], ascending=[False, False], na_position="last"))
stats = st.columns(2)
stats[0].metric("Stocks with signals", len(latest))
stats[1].metric("Setups / breakouts", f"{int(latest['signal'].eq('SETUP').sum())} / {int(latest['signal'].eq('BREAKOUT').sum())}")
if latest.empty:
    st.info("No signals match the selected filters. Try lowering the minimum score or clearing a filter.")
    st.stop()

names = company_names()
for _, signal_row in latest.iterrows():
    with st.container(border=False):
        render_card(signal_row, names.get(signal_row["symbol"], ""))
        if st.button("View analysis", key=f"view_{signal_row['symbol']}", width="stretch"):
            st.session_state.selected_symbol = signal_row["symbol"]
            st.rerun()

st.subheader("Market movers")
st.markdown("<div class='pp-note'>Top gainers and 1D/1W/1M performance are not shown because the application does not currently retrieve a market-wide price universe or period-return data for this view.</div>", unsafe_allow_html=True)
st.subheader("Signal history")
display = latest[["symbol", "date", "score", "classification", "signal", "status", "trend_qualified", "in_base", "breakout"]].copy()
display["score"] = display["score"].round(0).astype("Int64")
with st.container(key="desktop_history"):
    st.dataframe(display, hide_index=True, width="stretch", column_config={"date": st.column_config.DateColumn("Date", format="DD MMM YYYY"), "score": st.column_config.NumberColumn("VCP score", format="%d"), "trend_qualified": st.column_config.CheckboxColumn("Trend qualified"), "in_base": st.column_config.CheckboxColumn("In base"), "breakout": st.column_config.CheckboxColumn("Breakout")})
with st.container(key="mobile_history"):
    for _, history_row in display.iterrows():
        st.markdown(f"<div class='pp-card'><h3>{history_row['symbol']}</h3><div class='pp-muted'>{display_date(history_row['date'])} · {str(history_row['classification']).replace('_', ' ').title()}</div><div class='pp-value'>{history_row['signal']} · Score {history_row['score']}/100</div><div class='pp-muted'>Status: {history_row['status']} · Trend: {'Yes' if is_true(history_row['trend_qualified']) else 'No'} · Base: {'Yes' if is_true(history_row['in_base']) else 'No'} · Breakout: {'Yes' if is_true(history_row['breakout']) else 'No'}</div></div>", unsafe_allow_html=True)

with st.expander("Market context"):
    st.markdown("<div class='pp-note'>Index quotes, market news, and market-wide movers are not connected to the current data provider. No live or stale values are implied.</div>", unsafe_allow_html=True)
