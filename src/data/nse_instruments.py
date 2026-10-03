"""NSE equity instrument loader for PivotPulse."""

import gzip
import io

import pandas as pd
import requests


NSE_INSTRUMENTS_URL = (
    "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
)


def load_nse_equity_instruments() -> pd.DataFrame:
    """Load the current NSE equity instrument universe from Upstox."""

    response = requests.get(
        NSE_INSTRUMENTS_URL,
        timeout=60,
    )

    response.raise_for_status()

    content = response.content

    try:
        content = gzip.decompress(content)
    except gzip.BadGzipFile:
        pass

    data = pd.read_json(
        io.BytesIO(content)
    )

    data = data[
        (data["segment"] == "NSE_EQ")
        & (data["instrument_type"] == "EQ")
    ].copy()

    data = data[
        [
            "trading_symbol",
            "name",
            "instrument_key",
            "isin",
        ]
    ]

    return data.reset_index(drop=True)