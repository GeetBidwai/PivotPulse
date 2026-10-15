"""Multi-stock scanning for PivotPulse."""

from datetime import date, timedelta

import pandas as pd

from src.data.nse_instruments import load_nse_equity_instruments
from src.data.providers.upstox_provider import UpstoxMarketDataProvider
from src.early_vcp import analyze_early_vcp
from src.scanner import scan_historical


OUTPUT_COLUMNS = [
    "symbol",
    "date",
    "score",
    "classification",
    "signal",
    "status",
    "trend_qualified",
    "in_base",
    "breakout",
    "current_price",
    "latest_price",
    "latest_price_date",
    "pivot",
    "support",
    "atr_percent",
    "volume_contracting",
    "price_contracting",
    "pullbacks_percent",
    "reason",
]


WARM_UP_CALENDAR_DAYS = 400
MIN_HISTORY_ROWS = 252


NSE_MARKET_HOLIDAYS = frozenset(
    {
        date(2025, 2, 26),
        date(2025, 3, 14),
        date(2025, 3, 31),
        date(2025, 4, 10),
        date(2025, 4, 14),
        date(2025, 4, 18),
        date(2025, 5, 1),
        date(2025, 8, 15),
        date(2025, 8, 27),
        date(2025, 10, 2),
        date(2025, 10, 21),
        date(2025, 10, 22),
        date(2025, 11, 5),
        date(2025, 12, 25),
        date(2026, 1, 15),
        date(2026, 1, 26),
        date(2026, 3, 3),
        date(2026, 3, 26),
        date(2026, 3, 31),
        date(2026, 4, 3),
        date(2026, 4, 14),
        date(2026, 5, 1),
        date(2026, 5, 28),
        date(2026, 6, 26),
        date(2026, 9, 14),
        date(2026, 10, 2),
        date(2026, 10, 20),
        date(2026, 11, 10),
        date(2026, 11, 24),
        date(2026, 12, 25),
    }
)


def latest_completed_trading_day(
    selected_end_date: date,
    *,
    today: date | None = None,
    market_holidays: frozenset[date] = NSE_MARKET_HOLIDAYS,
) -> date:
    """Return the latest usable NSE trading date."""

    current_date = today or date.today()

    candidate = min(
        selected_end_date,
        current_date - timedelta(days=1),
    )

    while (
        candidate.weekday() >= 5
        or candidate in market_holidays
    ):
        candidate -= timedelta(days=1)

    return candidate


def prepare_scan_date_range(
    display_start_date: date,
    display_end_date: date,
    *,
    today: date | None = None,
    market_holidays: frozenset[date] = NSE_MARKET_HOLIDAYS,
) -> tuple[date, date]:
    """Build the raw market-data range including indicator warm-up."""

    return (
        display_start_date
        - timedelta(days=WARM_UP_CALENDAR_DAYS),
        latest_completed_trading_day(
            display_end_date,
            today=today,
            market_holidays=market_holidays,
        ),
    )


def filter_signals_to_display_range(
    results: pd.DataFrame,
    display_start_date: date,
    display_end_date: date,
) -> pd.DataFrame:
    """Keep only signals inside the selected display period."""

    if results.empty:
        return results.copy()

    signal_dates = pd.to_datetime(
        results["date"],
        utc=True,
    ).dt.tz_localize(None).dt.normalize()

    start = pd.Timestamp(display_start_date)
    end = pd.Timestamp(display_end_date)

    return results.loc[
        signal_dates.between(start, end)
    ].copy()


def scan_stocks(
    symbols: list[str],
    start_date: date,
    end_date: date,
    provider=None,
) -> pd.DataFrame:
    """Scan multiple NSE stocks and return VCP signals."""

    instruments = load_nse_equity_instruments()

    if provider is None:
        provider = UpstoxMarketDataProvider()

    scan_start_date, scan_end_date = prepare_scan_date_range(
        start_date,
        end_date,
    )

    results = []
    completed_symbols = 0
    errors = []

    for symbol in symbols:
        matches = instruments[
            instruments["trading_symbol"] == symbol
        ]

        if matches.empty:
            continue

        instrument_key = matches.iloc[0]["instrument_key"]

        try:
            df = provider.get_daily_data(
                symbol=instrument_key,
                start_date=scan_start_date,
                end_date=scan_end_date,
            )

            if df.empty:
                errors.append(f"{symbol}: no market data returned")
                continue

            df = df.sort_values("Date").reset_index(drop=True)

            latest_market_date = df["Date"].iloc[-1]
            latest_market_price = df["Close"].iloc[-1]


            completed_symbols += 1

            # -------------------------------------------------
            # Early VCP path for newly listed stocks
            # -------------------------------------------------

            if len(df) < MIN_HISTORY_ROWS:
                early_result = analyze_early_vcp(df)

                latest_date = (
                    df["Date"].iloc[-1]
                    if not df.empty
                    else pd.NaT
                )

                results.append(
                    {
                        "symbol": symbol,
                        "date": latest_date,
                        "score": early_result["confidence"],
                        "classification": "early_vcp",
                        "signal": early_result["signal"],
                        "status": "early_vcp",
                        "latest_price": latest_market_price,
                        "latest_price_date": latest_market_date,
                        "trend_qualified": early_result[
                            "trend_ok"
                        ],
                        "in_base": early_result[
                            "price_contracting"
                        ],
                        "breakout": early_result[
                            "breakout"
                        ],
                        "current_price": early_result[
                            "current_price"
                        ],
                        "pivot": early_result["pivot"],
                        "support": early_result["support"],
                        "atr_percent": early_result[
                            "atr_percent"
                        ],
                        "volume_contracting": early_result[
                            "volume_contracting"
                        ],
                        "price_contracting": early_result[
                            "price_contracting"
                        ],
                        "pullbacks_percent": early_result.get(
                            "pullbacks_percent", []
                        ),
                        "reason": early_result["reason"],
                    }
                )

                continue

            # -------------------------------------------------
            # Full VCP path
            # -------------------------------------------------


            historical = scan_historical(df)


            # Keep qualifying signals, but retain the calculated indicators.
            signals = historical.loc[
                historical["Signal"].str.lower() != "none"
            ].copy()

            for _, row in signals.iterrows():
                results.append(
                    {
                        "symbol": symbol,
                        "date": row["Date"],
                        "score": row["VCP_Score"],
                        "classification": row["VCP_Classification"],
                        "signal": str(row["Signal"]).lower(),
                        "status": "scanned",
                        "trend_qualified": row["Trend_Qualified"],
                        "in_base": row["In_Base"],
                        "breakout": row["Breakout"],
                        "current_price": row.get("Close", pd.NA),
                        "latest_price": latest_market_price,
                        "latest_price_date": latest_market_date,
                        "pivot": row.get("Pivot", pd.NA),
                        "support": row.get("Support", pd.NA),
                        "atr_percent": row.get("ATR_Pct", pd.NA),
                        "volume_contracting": pd.NA,
                        "price_contracting": pd.NA,
                        "pullbacks_percent": pd.NA,
                        "reason": (
                            f"Trend qualified: {bool(row['Trend_Qualified'])}; "
                            f"base identified: {bool(row['In_Base'])}; "
                            f"breakout: {bool(row['Breakout'])}."
                        ),
                    }
                )


            if signals.empty:
                results.append(
                    {
                        "symbol": symbol,
                        "date": latest_market_date,
                        "score": pd.NA,
                        "classification": "none",
                        "signal": "NONE",
                        "status": "no_signal",
                        "trend_qualified": pd.NA,
                        "in_base": pd.NA,
                        "breakout": pd.NA,
                        "current_price": pd.NA,
                        "latest_price": latest_market_price,
                        "latest_price_date": latest_market_date,
                        "pivot": pd.NA,
                        "support": pd.NA,
                        "atr_percent": pd.NA,
                        "volume_contracting": pd.NA,
                        "price_contracting": pd.NA,
                        "pullbacks_percent": pd.NA,
                        "reason": "No qualifying VCP signal in the scanned history.",
                    }
                )

           

        except (RuntimeError, ValueError) as error:
            errors.append(f"{symbol}: {error}")
            print(f"{symbol}: {error}")
            continue

    if errors and not completed_symbols:
        raise RuntimeError(
            "Unable to retrieve market data for the selected stocks. "
            f"{errors[0]}"
        )

    result = pd.DataFrame(
        results,
        columns=OUTPUT_COLUMNS,
    )

    if not result.empty:
        valid_signals = result[
            result["status"].isin(
                ["scanned", "early_vcp","no_signal"]
            )
        ]

        insufficient_history = result[
            result["status"] == "insufficient_history"
        ]

        valid_signals = filter_signals_to_display_range(
            valid_signals,
            start_date,
            end_date,
        )

        result = pd.concat(
            [
                valid_signals,
                insufficient_history,
            ],
            ignore_index=True,
        )

        result = (
            result
            .sort_values(
                ["date", "score"],
                ascending=[False, False],
                na_position="last",
            )
            .reset_index(drop=True)
        )

    return result