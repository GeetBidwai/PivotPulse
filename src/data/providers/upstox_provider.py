"""Upstox market-data provider for PivotPulse."""

from datetime import date

import pandas as pd
import requests

from src.data.providers.base import MarketDataProvider
from src.data.upstox_auth import get_upstox_access_token
from src.data_loader import validate_ohlcv


class UpstoxMarketDataProvider(MarketDataProvider):
    """Load daily OHLCV market data from Upstox."""

    BASE_URL = "https://api.upstox.com/v3/historical-candle"

    def get_daily_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """Fetch daily OHLCV data for an Upstox instrument key."""

        url = (
            f"{self.BASE_URL}/"
            f"{symbol}/days/1/"
            f"{end_date.isoformat()}/"
            f"{start_date.isoformat()}"
        )

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {get_upstox_access_token()}",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Upstox API request failed: "
                f"{response.status_code} - {response.text}"
            )

        payload = response.json()

        candles = payload.get("data", {}).get("candles", [])

        if not candles:
            raise ValueError(
                f"No candle data returned for instrument: {symbol}"
            )

        df = pd.DataFrame(
            candles,
            columns=[
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "OpenInterest",
            ],
        )

        df = df[
            [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]
        ]

        df["Date"] = pd.to_datetime(df["Date"])

        numeric_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        df = df.sort_values("Date")
        df = df.drop_duplicates(subset="Date")
        df = df.reset_index(drop=True)

        validate_ohlcv(df)

        return df