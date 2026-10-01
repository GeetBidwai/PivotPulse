"""Base detection for PivotPulse."""

import pandas as pd


def detect_base(
    df: pd.DataFrame,
    min_duration: int = 15,
    max_duration: int = 120,
) -> pd.DataFrame:
    """
    Identify potential consolidation periods.

    A base is considered a period where the price remains within
    a controlled range for a meaningful number of trading sessions.
    """

    if min_duration < 1:
        raise ValueError("min_duration must be at least 1.")

    if max_duration < min_duration:
        raise ValueError(
            "max_duration must be greater than or equal to min_duration."
        )

    result = df.copy()

    rolling_high = result["High"].rolling(min_duration).max()
    rolling_low = result["Low"].rolling(min_duration).min()

    result["Base_Range"] = (
        (rolling_high - rolling_low) / rolling_low
    )

    result["In_Base"] = (
        result["Base_Range"] <= 0.30
    )

    return result