"""Tests for base detection."""

import pandas as pd

from src.base_detector import detect_base


def test_detect_base():
    """Verify that a controlled price range is identified as a base."""

    df = pd.DataFrame(
        {
            "High": [100, 102, 101, 103, 102, 101, 104, 103, 102, 103,
                     101, 102, 104, 103, 102],
            "Low": [98, 99, 98, 100, 99, 98, 100, 99, 98, 100,
                    99, 98, 100, 99, 98],
        }
    )

    result = detect_base(
        df,
        min_duration=5,
        max_duration=120,
    )

    assert result["Base_Range"].notna().any()
    assert result["In_Base"].any()