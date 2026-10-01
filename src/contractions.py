"""Contraction analysis for PivotPulse."""

import pandas as pd


def calculate_contractions(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate pullback depth between consecutive swing highs and lows.

    Contraction depth is measured as:

        (swing_high - following_swing_low) / swing_high
    """

    result = df.copy()

    result["Contraction_Depth"] = pd.NA

    swing_high_indices = result.index[
        result["Swing_High"]
    ].tolist()

    for high_index in swing_high_indices:
        following_lows = result.index[
            (result.index > high_index)
            & result["Swing_Low"]
        ]

        if len(following_lows) == 0:
            continue

        low_index = following_lows[0]

        high_price = result.loc[high_index, "High"]
        low_price = result.loc[low_index, "Low"]

        if high_price > 0:
            result.loc[low_index, "Contraction_Depth"] = (
                (high_price - low_price) / high_price
            )

    result["Contraction_Depth"] = pd.to_numeric(
        result["Contraction_Depth"],
        errors="coerce",
    )

    return result