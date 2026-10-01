"""Tests for breakout detection."""

import pandas as pd

from src.breakout import detect_breakouts


def test_detect_breakout_with_volume_confirmation():
    """Verify a breakout requires price and volume confirmation."""

    df = pd.DataFrame(
        {
            "Close": [100, 106, 108],
            "Pivot": [105, 105, 107],
            "RelativeVolume": [1.0, 1.6, 1.2],
        }
    )

    result = detect_breakouts(
        df,
        breakout_multiplier=1.5,
    )

    assert result.loc[1, "Breakout"]
    assert not result.loc[2, "Breakout"]