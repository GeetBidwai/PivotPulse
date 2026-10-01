"""Breakout detection for PivotPulse."""

import pandas as pd


def detect_breakouts(
    df: pd.DataFrame,
    breakout_multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Identify potential breakouts above the previous pivot.

    A breakout requires:
    - Close above the previous pivot.
    - Relative volume meeting the configured multiplier.
    """

    if breakout_multiplier <= 0:
        raise ValueError("breakout_multiplier must be greater than 0.")

    result = df.copy()

    result["Breakout"] = (
        (result["Close"] > result["Pivot"].shift(1))
        & (
            result["RelativeVolume"]
            >= breakout_multiplier
        )
    )

    result["Breakout"] = result["Breakout"].fillna(False)

    return result