"""Universe filtering for PivotPulse."""

import pandas as pd


def passes_universe_filter(
    df: pd.DataFrame,
    min_price: float = 50,
    min_average_turnover: float = 50_000_000,
    average_period: int = 20,
) -> bool:
    """Check whether a stock meets the basic universe liquidity filters."""

    if df.empty:
        return False

    if len(df) < average_period:
        return False

    latest_close = df["Close"].iloc[-1]

    average_turnover = (
        (df["Close"] * df["Volume"])
        .rolling(average_period)
        .mean()
        .iloc[-1]
    )

    return bool(
        latest_close >= min_price
        and average_turnover >= min_average_turnover
    )