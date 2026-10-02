"""Tests for universe scanning."""

from datetime import date

import pandas as pd

from src.universe_scanner import scan_universe


class FakeProvider:
    """Simple provider used for testing."""

    def __init__(self, data):
        self.data = data

    def get_daily_data(self, symbol, start_date, end_date):
        return self.data[symbol]


def test_scan_universe(monkeypatch):
    """Verify that only stocks passing the universe filter are returned."""

    passing_df = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=20),
            "Close": [100.0] * 20,
            "Volume": [1_000_000] * 20,
        }
    )

    failing_df = pd.DataFrame(
        {
            "Date": pd.date_range("2026-01-01", periods=20),
            "Close": [40.0] * 20,
            "Volume": [1_000_000] * 20,
        }
    )

    data = {
        "PASS": passing_df,
        "FAIL": failing_df,
    }

    monkeypatch.setattr(
        "src.universe_scanner.CSVMarketDataProvider",
        lambda data_directory: FakeProvider(data),
    )

    result = scan_universe(
        symbols=["PASS", "FAIL"],
        data_directory="data/raw",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert result == ["PASS"]