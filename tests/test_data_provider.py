"""Tests for the CSV market-data provider."""

from datetime import date
from pathlib import Path

from src.data.providers.csv_provider import CSVMarketDataProvider


def test_csv_provider_loads_data():
    """Verify that CSV provider loads valid OHLCV data."""

    project_root = Path(__file__).resolve().parents[1]

    provider = CSVMarketDataProvider(
        project_root / "data" / "raw"
    )

    df = provider.get_daily_data(
        symbol="TEST",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
    )

    assert len(df) == 3
    assert list(df.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]