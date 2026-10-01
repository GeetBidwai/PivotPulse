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