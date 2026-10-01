"""Pivot detection for PivotPulse."""

import pandas as pd


def detect_pivot(
    df: pd.DataFrame,
    lookback: int = 20,
) -> pd.DataFrame:
    """
    Identify the recent resistance level used as a potential pivot.

    The pivot is the highest high over the specified lookback period.
    """

    if lookback < 1:
        raise ValueError("lookback must be at least 1.")

    result = df.copy()

    result["Pivot"] = (
        result["High"]
        .rolling(lookback)
        .max()
    )

    return result