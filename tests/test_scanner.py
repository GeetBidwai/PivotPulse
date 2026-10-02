"""Tests for the VCP scanner."""

import pandas as pd

from src.scanner import scan_stock


def test_scan_stock_returns_expected_structure():
    """Verify the scanner runs end-to-end and returns expected fields."""

    df = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=260, freq="D"),
            "Open": [100.0] * 260,
            "High": [105.0] * 260,
            "Low": [95.0] * 260,
            "Close": [100.0] * 260,
            "Volume": [1_000_000] * 260,
        }
    )

    result = scan_stock(df)

    expected_keys = {
        "score",
        "contraction_score",
        "tightening_score",
        "final_contraction_score",
        "volatility_score",
        "volume_score",
        "trend_qualified",
        "in_base",
        "breakout",
        "data",
    }

    assert expected_keys.issubset(result.keys())
    assert 0 <= result["score"] <= 100
    assert isinstance(result["data"], pd.DataFrame)