"""CSV-based market-data provider for PivotPulse."""

from datetime import date
from pathlib import Path

import pandas as pd

from src.data.providers.base import MarketDataProvider
from src.data_loader import validate_ohlcv


class CSVMarketDataProvider(MarketDataProvider):
    """Load market data from a local CSV file."""

    def __init__(self, data_directory: str | Path):
        """Initialize the provider with a CSV data directory."""

        self.data_directory = Path(data_directory)

    def get_daily_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Load and filter daily OHLCV data for a symbol."""

        file_path = self.data_directory / f"{symbol}.csv"

        if not file_path.exists():
            raise FileNotFoundError(
                f"No CSV data found for symbol: {symbol}"
            )

        df = pd.read_csv(file_path)

        required_columns = [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        df["Date"] = pd.to_datetime(df["Date"])

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        df = df[
            (df["Date"] >= start)
            & (df["Date"] <= end)
        ].copy()

        df = df.sort_values("Date")
        df = df.drop_duplicates(subset="Date")
        df = df.reset_index(drop=True)

        validate_ohlcv(df)

        return df