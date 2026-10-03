"""Multi-stock scanning for PivotPulse."""

from datetime import date

import pandas as pd

from src.data.nse_instruments import load_nse_equity_instruments
from src.data.providers.upstox_provider import UpstoxMarketDataProvider
from src.scanner import scan_historical


def scan_stocks(
    symbols: list[str],
    start_date: date,
    end_date: date,
    provider=None,
) -> pd.DataFrame:
    """Scan multiple NSE stocks using historical market data."""

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

            if signals.empty:
                continue

            latest = signals.iloc[-1]

            results.append(
                {
                    "symbol": symbol,
                    "date": latest["Date"],
                    "score": latest["VCP_Score"],
                    "classification": latest[
                        "VCP_Classification"
                    ],
                    "signal": latest["Signal"],
                    "trend_qualified": latest[
                        "Trend_Qualified"
                    ],
                    "in_base": latest["In_Base"],
                    "breakout": latest["Breakout"],
                }
            )

        except (RuntimeError, ValueError) as error:
            print(f"{symbol}: {error}")
            continue

    return pd.DataFrame(results)