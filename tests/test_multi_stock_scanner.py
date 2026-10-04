"""Tests for multi-stock scanning."""

from datetime import date

import pandas as pd

import src.multi_stock_scanner as scanner


class FakeProvider:
    """Return controlled market data without calling Upstox."""

    def __init__(self, data):
        self.data = data

    def get_daily_data(
        self,
        symbol,
        start_date,
        end_date,
    ):
        return self.data


def make_sample_data():
    """Create simple OHLCV data for the provider test."""

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


def test_scan_stocks_accepts_custom_provider(monkeypatch):
    """Verify multi-stock scanning can use an injected provider."""

    instruments = pd.DataFrame(
        {
            "trading_symbol": ["TEST"],
            "name": ["TEST COMPANY"],
            "instrument_key": ["NSE_EQ|TEST"],
            "isin": ["TESTISIN"],
        }
    )

    monkeypatch.setattr(
        scanner,
        "load_nse_equity_instruments",
        lambda: instruments,
    )

    provider = FakeProvider(make_sample_data())

    result = scanner.scan_stocks(
        symbols=["TEST"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 9, 30),
        provider=provider,
    )

    assert isinstance(result, pd.DataFrame)


def test_scan_stocks_returns_all_historical_signals(monkeypatch):
    """Verify all non-none historical signals are returned."""

    instruments = pd.DataFrame(
        {
            "trading_symbol": ["TEST"],
            "name": ["TEST COMPANY"],
            "instrument_key": ["NSE_EQ|TEST"],
            "isin": ["TESTISIN"],
        }
    )

    monkeypatch.setattr(
        scanner,
        "load_nse_equity_instruments",
        lambda: instruments,
    )

    historical = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                [
                    "2025-01-01",
                    "2025-01-02",
                    "2025-01-03",
                ]
            ),
            "VCP_Score": [0, 82, 91],
            "VCP_Classification": [
                "none",
                "strong",
                "strong",
            ],
            "Signal": [
                "none",
                "setup",
                "breakout",
            ],
            "Trend_Qualified": [
                False,
                True,
                True,
            ],
            "In_Base": [
                False,
                True,
                False,
            ],
            "Breakout": [
                False,
                False,
                True,
            ],
        }
    )

    monkeypatch.setattr(
        scanner,
        "scan_historical",
        lambda df: historical,
    )

    provider = FakeProvider(make_sample_data())

    result = scanner.scan_stocks(
        symbols=["TEST"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 9, 30),
        provider=provider,
    )

    assert len(result) == 2

    assert result["symbol"].tolist() == [
        "TEST",
        "TEST",
    ]

    assert result["signal"].tolist() == [
        "breakout",
        "setup",
    ]

    assert result["score"].tolist() == [
        91,
        82,
    ]