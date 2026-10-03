"""Contraction analysis for PivotPulse."""

import pandas as pd


def calculate_contractions(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate pullback depth between consecutive swing highs and lows
    that occur inside the same base.

    A swing high is paired only with the first following swing low
    before another swing high occurs.

    Both the swing high and swing low must belong to the same base.
    """

    result = df.copy()

    result["Contraction_Depth"] = pd.NA

    base_mask = result["In_Base"]

    swing_high_indices = result.index[
        result["Swing_High"] & base_mask
    ].tolist()

    for high_index in swing_high_indices:
        following_indices = result.index[
            result.index > high_index
        ]

        for index in following_indices:
            if result.loc[index, "Swing_High"]:
                break

            if result.loc[index, "Swing_Low"]:
                if not result.loc[index, "In_Base"]:
                    break

                high_price = result.loc[high_index, "High"]
                low_price = result.loc[index, "Low"]

                if high_price > 0:
                    result.loc[index, "Contraction_Depth"] = (
                        (high_price - low_price) / high_price
                    )

                break

    result["Contraction_Depth"] = pd.to_numeric(
        result["Contraction_Depth"],
        errors="coerce",
    )

    return result