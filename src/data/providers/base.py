"""Base interface for PivotPulse market-data providers."""

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class MarketDataProvider(ABC):
    """Abstract interface for historical and market-data providers."""

    @abstractmethod
    def get_daily_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        Return daily OHLCV data for a symbol.

        The returned DataFrame must contain:
        Date, Open, High, Low, Close, Volume
        """

        raise NotImplementedError