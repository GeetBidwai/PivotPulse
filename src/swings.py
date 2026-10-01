"""Swing high and swing low detection for PivotPulse."""

import pandas as pd


def detect_swings(
    df: pd.DataFrame,
    lookback: int = 3,
) -> pd.DataFrame:
    """
    Detect local swing highs and swing lows.

    A swing high is a high greater than the highs of the
    surrounding lookback window.

    A swing low is a low lower than the lows of the
    surrounding lookback window.
    """

    if lookback < 1:
        raise ValueError("lookback must be at least 1.")

    result = df.copy()

    window = (2 * lookback) + 1

    result["Swing_High"] = (
        result["High"]
        == result["High"].rolling(window, center=True).max()
    )

    result["Swing_Low"] = (
        result["Low"]
        == result["Low"].rolling(window, center=True).min()
    )

    result["Swing_High"] = result["Swing_High"].fillna(False)
    result["Swing_Low"] = result["Swing_Low"].fillna(False)

    return result