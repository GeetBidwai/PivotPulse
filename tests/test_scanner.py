"""Tests for the VCP scanner."""

import pandas as pd

from src.scanner import scan_stock


def make_sample_data():
    """Create sample OHLCV data for scanner tests."""

    return pd.DataFrame(
        {
            "Date": pd.date_range(
                "2025-01-01",
                periods=260,
                freq="D",
            ),
            "Open": [100.0] * 260,
            "High": [105.0] * 260,
            "Low": [95.0] * 260,
            "Close": [100.0] * 260,
            "Volume": [1_000_000] * 260,
        }
    )


def test_scan_stock_returns_expected_structure():
    """Verify the scanner returns the expected fields."""

    df = make_sample_data()

    result = scan_stock(df)

    expected_keys = {
        "score",
        "classification",
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
    assert result["classification"] in {
        "none",
        "candidate",
        "strong",
    }
    assert isinstance(result["data"], pd.DataFrame)


def test_scanner_passes_base_configuration(monkeypatch):
    """Verify that YAML base settings reach the base detector."""

    import src.scanner as scanner

    df = make_sample_data()

    captured = {}

    original_detect_base = scanner.detect_base

    def spy_detect_base(
        data,
        min_duration,
        max_duration,
        max_net_decline,
    ):
        captured["min_duration"] = min_duration
        captured["max_duration"] = max_duration
        captured["max_net_decline"] = max_net_decline

        return original_detect_base(
            data,
            min_duration=min_duration,
            max_duration=max_duration,
            max_net_decline=max_net_decline,
        )

    monkeypatch.setattr(
        scanner,
        "detect_base",
        spy_detect_base,
    )

    config = scanner.load_config()

    scanner.scan_stock(df)

    assert captured["min_duration"] == (
        config["base"]["min_duration_days"]
    )

    assert captured["max_duration"] == (
        config["base"]["max_duration_days"]
    )

    assert captured["max_net_decline"] == (
        config["base"]["max_net_decline"]
    )