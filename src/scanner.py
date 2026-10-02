"""VCP scanner orchestration for PivotPulse."""

import pandas as pd

from src.config import load_config

from src.base_detector import detect_base
from src.breakout import detect_breakouts
from src.contractions import calculate_contractions
from src.indicators import add_indicators
from src.pivot import detect_pivot
from src.swings import detect_swings
from src.trend import qualify_trend
from src.vcp_score import score_vcp


def scan_stock(df: pd.DataFrame) -> dict:
    """Run the initial PivotPulse VCP scanning pipeline."""

    config = load_config()

    result = add_indicators(
        df,
        fast_sma=config["trend"]["fast_sma"],
        slow_sma=config["trend"]["slow_sma"],
        atr_period=config["volatility"]["atr_period"],
        volume_period=config["volume"]["average_period"],
    )

    result = qualify_trend(
        result,
        fast_sma=config["trend"]["fast_sma"],
        slow_sma=config["trend"]["slow_sma"],
        max_distance_from_52w_high=config["trend"]["max_distance_from_52w_high"],
    )

    result = detect_swings(
        result,
        lookback=config["swings"]["lookback"],
    )

    result = detect_base(
        result,
        min_duration=config["base"]["min_duration_days"],
        max_duration=config["base"]["max_duration_days"],
    )

    result = calculate_contractions(result)

    result = detect_pivot(
        result,
        lookback=config["pivot"]["lookback"],
    )

    result = detect_breakouts(
        result,
        breakout_multiplier=config["volume"]["breakout_multiplier"],
    )

    latest = result.iloc[-1]
    active_base = result.iloc[0:0]

    if latest["In_Base"] and pd.notna(latest["Base_Start"]):
        active_base = result[
            (result["Date"] >= latest["Base_Start"])
            & result["In_Base"]
        ]

        contraction_depths = (
            active_base["Contraction_Depth"]
            .dropna()
            .tolist()
        )
    else:
        contraction_depths = []

    vcp_result = score_vcp(
        contraction_depths,
        final_contraction_max_depth=config["vcp"]["final_contraction_max_depth"],
        atr_pcts=active_base["ATR_Pct"].dropna().tolist(),
        relative_volumes=active_base["RelativeVolume"].dropna().tolist(),
    )

    latest = result.iloc[-1]

    return {
        "score": vcp_result["score"],
        "contraction_score": vcp_result["contraction_score"],
        "tightening_score": vcp_result["tightening_score"],
        "final_contraction_score": vcp_result[
            "final_contraction_score"
        ],
        "volatility_score": vcp_result["volatility_score"],
        "volume_score": vcp_result["volume_score"],
        "trend_qualified": bool(
            latest["Trend_Qualified"]
        ),
        "in_base": bool(
            latest["In_Base"]
        ),
        "breakout": bool(
            latest["Breakout"]
        ),
        "data": result,
    }