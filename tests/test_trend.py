"""Tests for trend qualification."""

import pandas as pd

from src.trend import qualify_trend


def test_trend_qualification():
    """Verify a stock meeting the trend rules is qualified."""

    df = pd.DataFrame(
        {
            "Close": [120, 125, 130, 135, 140, 145],
            "SMA_50": [110, 112, 115, 118, 120, 125],
            "SMA_200": [100, 101, 102, 103, 104, 105],
            "Distance_From_52W_High": [
                -0.10, -0.09, -0.08, -0.07, -0.06, -0.05
            ],
        }
    )

    result = qualify_trend(df)

    assert result.loc[5, "Trend_Qualified"]


def test_trend_rejects_price_below_sma():
    """Verify that price below the 50-DMA is rejected."""

    df = pd.DataFrame(
        {
            "Close": [90, 91, 92, 93, 94, 95],
            "SMA_50": [100, 101, 102, 103, 104, 105],
            "SMA_200": [90, 91, 92, 93, 94, 95],
            "Distance_From_52W_High": [
                -0.10, -0.09, -0.08, -0.07, -0.06, -0.05
            ],
        }
    )

    result = qualify_trend(df)

    assert not result.loc[5, "Trend_Qualified"]