"""Core market-data models used by PivotPulse."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OHLCVRecord:
    """Represent one OHLCV market-data record."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float