"""Tests for base detection."""

import pandas as pd

from src.base_detector import detect_base


def test_detect_base():
    """Verify that a controlled price range is identified as a base."""

    df = pd.DataFrame(
        {
            "High": [
                100, 102, 101, 103, 102,
                101, 104, 103, 102, 103,
                101, 102, 104, 103, 102,
            ],
            "Low": [
                98, 99, 98, 100, 99,
                98, 100, 99, 98, 100,
                99, 98, 100, 99, 98,
            ],
            "Close": [
                99, 101, 100, 102, 101,
                100, 102, 101, 100, 102,
                100, 101, 102, 101, 100,
            ],
        }
    )

    result = detect_base(
        df,
        min_duration=5,
        max_duration=120,
    )

    assert result["In_Base"].any()
    assert result["Base_Range"].notna().any()


def test_rejects_steady_decline():
    """Verify that a persistent decline is not treated as a base."""

    df = pd.DataFrame(
        {
            "High": [
                100, 99, 98, 97, 96,
                95, 94, 93, 92, 91,
            ],
            "Low": [
                98, 97, 96, 95, 94,
                93, 92, 91, 90, 89,
            ],
            "Close": [
                99, 98, 97, 96, 95,
                94, 93, 92, 91, 90,
            ],
        }
    )

    result = detect_base(
        df,
        min_duration=5,
        max_duration=120,
        max_net_decline=0.15,
    )

    assert not result["In_Base"].any()


def test_detects_upward_consolidation():
    """Verify that a controlled upward consolidation can be a base."""

    df = pd.DataFrame(
        {
            "High": [
                100, 103, 102, 105, 104,
                106, 105, 108, 107, 109,
            ],
            "Low": [
                98, 100, 99, 102, 101,
                103, 102, 105, 104, 106,
            ],
            "Close": [
                99, 102, 101, 104, 103,
                105, 104, 107, 106, 108,
            ],
        }
    )

    result = detect_base(
        df,
        min_duration=5,
        max_duration=120,
    )

    assert result["In_Base"].any()