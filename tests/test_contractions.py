"""Tests for contraction analysis."""

import pandas as pd

from src.contractions import calculate_contractions


def test_calculate_contractions():
    """Verify contraction depth is calculated correctly."""

    df = pd.DataFrame(
        {
            "High": [100, 95, 90, 85],
            "Low": [98, 80, 88, 70],
            "Swing_High": [True, False, True, False],
            "Swing_Low": [False, True, False, True],
            "In_Base": [True, True, True, True],
        }
    )

    result = calculate_contractions(df)

    assert result.loc[1, "Contraction_Depth"] == 0.20
    assert result.loc[3, "Contraction_Depth"] == 0.2222222222222222


def test_ignores_low_outside_base():
    """Verify a swing low outside the base is not used."""

    df = pd.DataFrame(
        {
            "High": [100, 95, 105, 98],
            "Low": [98, 80, 100, 70],
            "Swing_High": [True, False, True, False],
            "Swing_Low": [False, True, False, True],
            "In_Base": [True, False, True, False],
        }
    )

    result = calculate_contractions(df)

    assert pd.isna(result.loc[1, "Contraction_Depth"])
    assert pd.isna(result.loc[3, "Contraction_Depth"])


def test_does_not_cross_intervening_out_of_base_swing_high():
    """Verify a contraction does not cross an intervening out-of-base swing high."""

    df = pd.DataFrame(
        {
            "High": [100, 120, 105],
            "Low": [98, 118, 80],
            "Swing_High": [True, True, False],
            "Swing_Low": [False, False, True],
            "In_Base": [True, False, True],
        }
    )

    result = calculate_contractions(df)

    assert pd.isna(result.loc[2, "Contraction_Depth"])