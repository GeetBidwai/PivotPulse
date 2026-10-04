"""Multi-stock scanning for PivotPulse."""

from datetime import date, timedelta

import pandas as pd

from src.data.nse_instruments import load_nse_equity_instruments
from src.data.providers.upstox_provider import UpstoxMarketDataProvider
from src.scanner import scan_historical


OUTPUT_COLUMNS = [
    "symbol",
    "date",
    "score",
    "classification",
    "signal",
    "trend_qualified",
    "in_base",
    "breakout",
]

WARM_UP_CALENDAR_DAYS = 400

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
    """Scan multiple NSE stocks for signals in the selected period."""

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

            completed_symbols += 1

            historical = scan_historical(df)

            signals = historical[
                historical["Signal"] != "none"
            ]

            for _, row in signals.iterrows():
                results.append(
                    {
                        "symbol": symbol,
                        "date": row["Date"],
                        "score": row["VCP_Score"],
                        "classification": row[
                            "VCP_Classification"
                        ],
                        "signal": row["Signal"],
                        "trend_qualified": row[
                            "Trend_Qualified"
                        ],
                        "in_base": row["In_Base"],
                        "breakout": row["Breakout"],
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

    result = filter_signals_to_display_range(
        result,
        start_date,
        end_date,
    )

    if not result.empty:
        result = (
            result
            .sort_values(
                ["date", "score"],
                ascending=[False, False],
            )
            .reset_index(drop=True)
        )

    return result