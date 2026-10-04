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


def test_prepare_scan_date_range_adds_warm_up_history():
    """The market-data request includes history before the display period."""

    market_start, market_end = scanner.prepare_scan_date_range(
        date(2025, 6, 1),
        date(2025, 6, 20),
        today=date(2025, 6, 21),
    )

    assert market_start == date(2024, 4, 27)
    assert market_end == date(2025, 6, 20)


def test_prepare_scan_date_range_caps_today_and_holidays():
    """Incomplete, weekend, and known holiday dates use the prior trading day."""

    _, today_end = scanner.prepare_scan_date_range(
        date(2025, 1, 1),
        date(2025, 1, 27),
        today=date(2025, 1, 27),
    )
    _, holiday_end = scanner.prepare_scan_date_range(
        date(2025, 1, 1),
        date(2025, 2, 26),
        today=date(2025, 2, 27),
    )

    assert today_end == date(2025, 1, 24)
    assert holiday_end == date(2025, 2, 25)


def test_filter_signals_to_display_range_keeps_only_selected_dates():
    """Warm-up-period signals are not displayed to the user."""

    results = pd.DataFrame(
        {
            "symbol": ["TEST", "TEST", "TEST"],
            "date": pd.to_datetime(["2025-01-31", "2025-02-01", "2025-02-28"]),
            "score": [80, 85, 90],
        }
    )

    filtered = scanner.filter_signals_to_display_range(
        results,
        date(2025, 2, 1),
        date(2025, 2, 27),
    )

    assert filtered["date"].tolist() == [pd.Timestamp("2025-02-01")]
