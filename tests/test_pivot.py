"""Tests for pivot detection."""

import pandas as pd

from src.pivot import detect_pivot


def test_detect_pivot():
    """Verify that the rolling high is used as the pivot."""

    df = pd.DataFrame(
        {
            "High": [100, 105, 103, 110, 107],
        }
    )

    result = detect_pivot(df, lookback=3)

    assert pd.isna(result.loc[1, "Pivot"])
    assert result.loc[2, "Pivot"] == 105
    assert result.loc[3, "Pivot"] == 110
    assert result.loc[4, "Pivot"] == 110