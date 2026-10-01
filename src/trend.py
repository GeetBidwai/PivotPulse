"""Trend qualification for PivotPulse."""

import pandas as pd


def qualify_trend(
    df: pd.DataFrame,
    fast_sma: int = 50,
    slow_sma: int = 200,
    max_distance_from_52w_high: float = 0.15,
) -> pd.DataFrame:
    """Identify rows that satisfy the initial VCP trend conditions."""

    result = df.copy()

    fast_column = f"SMA_{fast_sma}"
    slow_column = f"SMA_{slow_sma}"

    fast_sma_rising = (
        result[fast_column] > result[fast_column].shift(5)
    )

    result["Trend_Qualified"] = (
        (result["Close"] > result[fast_column])
        & (result["Close"] > result[slow_column])
        & (result[fast_column] > result[slow_column])
        & fast_sma_rising
        & (
            result["Distance_From_52W_High"]
            >= -max_distance_from_52w_high
        )
    )

    result["Trend_Qualified"] = (
        result["Trend_Qualified"].fillna(False)
    )

    return result