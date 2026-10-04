"""Multi-stock scanning for PivotPulse."""

from datetime import date

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


def scan_stocks(
    symbols: list[str],
    start_date: date,
    end_date: date,
    provider=None,
) -> pd.DataFrame:
    """Scan multiple NSE stocks and return frontend-ready signals."""

    instruments = load_nse_equity_instruments()

    if provider is None:
        provider = UpstoxMarketDataProvider()

    results = []

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
                start_date=start_date,
                end_date=end_date,
            )

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
            print(f"{symbol}: {error}")
            continue

    result = pd.DataFrame(
        results,
        columns=OUTPUT_COLUMNS,
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