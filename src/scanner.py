"""VCP scanner orchestration for PivotPulse."""

import pandas as pd

from src.base_detector import detect_base
from src.breakout import detect_breakouts
from src.contractions import calculate_contractions
from src.indicators import add_indicators
from src.pivot import detect_pivot
from src.swings import detect_swings
from src.trend import qualify_trend
from src.vcp_score import score_vcp


def scan_stock(
    df: pd.DataFrame,
    fast_sma: int = 50,
    slow_sma: int = 200,
    atr_period: int = 14,
    volume_period: int = 20,
    base_min_duration: int = 15,
    base_max_duration: int = 120,
    breakout_multiplier: float = 1.5,
    final_contraction_max_depth: float = 0.10,
    max_distance_from_52w_high: float = 0.15,
) -> dict:
    """Run the initial PivotPulse VCP scanning pipeline."""

    result = add_indicators(
        df,
        fast_sma=fast_sma,
        slow_sma=slow_sma,
        atr_period=atr_period,
        volume_period=volume_period,
    )

    result = qualify_trend(
        result,
        fast_sma=fast_sma,
        slow_sma=slow_sma,
        max_distance_from_52w_high=max_distance_from_52w_high,
    )

    result = detect_swings(result)

    result = detect_base(
        result,
        min_duration=base_min_duration,
        max_duration=base_max_duration,
    )

    result = calculate_contractions(result)

    result = detect_pivot(result)

    result = detect_breakouts(
        result,
        breakout_multiplier=breakout_multiplier,
    )

    contraction_depths = (
        result["Contraction_Depth"]
        .dropna()
        .tolist()
    )

    vcp_result = score_vcp(
        contraction_depths,
        final_contraction_max_depth=final_contraction_max_depth,
    )

    latest = result.iloc[-1]

    return {
        "score": vcp_result["score"],
        "contraction_score": vcp_result["contraction_score"],
        "tightening_score": vcp_result["tightening_score"],
        "final_contraction_score": vcp_result[
            "final_contraction_score"
        ],
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