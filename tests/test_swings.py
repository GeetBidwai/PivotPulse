"""Tests for swing detection."""

import pandas as pd

from src.swings import detect_swings


def test_detect_swings():
    """Verify that local swing highs and lows are detected."""

    df = pd.DataFrame(
        {
            "High": [10, 11, 15, 12, 13],
            "Low": [8, 9, 11, 8, 10],
        }
    )

    result = detect_swings(df, lookback=1)

    assert result.loc[2, "Swing_High"] == True
    assert result.loc[3, "Swing_Low"] == True