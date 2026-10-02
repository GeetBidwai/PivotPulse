"""Tests for universe filtering."""

import pandas as pd

from src.universe import passes_universe_filter


def test_passes_universe_filter():
    """Verify a stock meeting the filters passes."""

    df = pd.DataFrame(
        {
            "Close": [100.0] * 20,
            "Volume": [1_000_000] * 20,
        }
    )

    assert passes_universe_filter(df) is True


def test_fails_price_filter():
    """Verify a stock below the minimum price fails."""

    df = pd.DataFrame(
        {
            "Close": [40.0] * 20,
            "Volume": [2_000_000] * 20,
        }
    )

    assert passes_universe_filter(df) is False


def test_fails_turnover_filter():
    """Verify a stock with insufficient turnover fails."""

    df = pd.DataFrame(
        {
            "Close": [100.0] * 20,
            "Volume": [100_000] * 20,
        }
    )

    assert passes_universe_filter(df) is False