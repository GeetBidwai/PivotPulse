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


def classify_signal(
    score: int,
    trend_qualified: bool,
    in_base: bool,
    breakout: bool,
    candidate_score: int,
) -> str:
    """Classify the current VCP setup state."""

    if breakout and trend_qualified:
        return "breakout"

    if (
        score >= candidate_score
        and trend_qualified
        and in_base
    ):
        return "setup"

    return "none"


def _run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """Run all indicator and pattern calculations."""

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
        max_distance_from_52w_high=config["trend"][
            "max_distance_from_52w_high"
        ],
    )

    result = detect_swings(
        result,
        lookback=config["swings"]["lookback"],
    )

    result = detect_base(
        result,
        min_duration=config["base"]["min_duration_days"],
        max_duration=config["base"]["max_duration_days"],
        max_net_decline=config["base"]["max_net_decline"],
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

    return result


def _score_row(
    result: pd.DataFrame,
    row_index: int,
) -> dict:
    """Score the active base at a specific historical row."""

    config = load_config()

    row = result.iloc[row_index]

    if row["In_Base"] and pd.notna(row["Base_Start"]):
        active_base = result.iloc[: row_index + 1]

        active_base = active_base[
            (active_base["Date"] >= row["Base_Start"])
            & active_base["In_Base"]
        ]

        contraction_depths = (
            active_base["Contraction_Depth"]
            .dropna()
            .tolist()
        )

        atr_pcts = (
            active_base["ATR_Pct"]
            .dropna()
            .tolist()
        )

        relative_volumes = (
            active_base["RelativeVolume"]
            .dropna()
            .tolist()
        )
    else:
        contraction_depths = []
        atr_pcts = []
        relative_volumes = []

    return score_vcp(
        contraction_depths,
        final_contraction_max_depth=config["vcp"][
            "final_contraction_max_depth"
        ],
        min_contractions=config["base"]["min_contractions"],
        max_contractions=config["base"]["max_contractions"],
        atr_pcts=atr_pcts,
        relative_volumes=relative_volumes,
    )


def scan_stock(df: pd.DataFrame) -> dict:
    """Run the PivotPulse VCP scanning pipeline."""

    config = load_config()

    result = _run_pipeline(df)

    latest = result.iloc[-1]

    vcp_result = _score_row(
        result,
        len(result) - 1,
    )

    score = vcp_result["score"]

    candidate_score = config["vcp"]["candidate_score"]
    strong_score = config["vcp"]["strong_score"]

    if score >= strong_score:
        classification = "strong"
    elif score >= candidate_score:
        classification = "candidate"
    else:
        classification = "none"

    trend_qualified = bool(
        latest["Trend_Qualified"]
    )

    in_base = bool(
        latest["In_Base"]
    )

    breakout = bool(
        latest["Breakout"]
    )

    signal = classify_signal(
        score=score,
        trend_qualified=trend_qualified,
        in_base=in_base,
        breakout=breakout,
        candidate_score=candidate_score,
    )

    return {
        "score": score,
        "classification": classification,
        "signal": signal,
        "contraction_score": vcp_result["contraction_score"],
        "tightening_score": vcp_result["tightening_score"],
        "final_contraction_score": vcp_result[
            "final_contraction_score"
        ],
        "volatility_score": vcp_result["volatility_score"],
        "volume_score": vcp_result["volume_score"],
        "trend_qualified": trend_qualified,
        "in_base": in_base,
        "breakout": breakout,
        "data": result,
    }


def scan_historical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scan historical rows and return VCP state for each trading day.
    """

    config = load_config()

    result = _run_pipeline(df)

    scores = []
    classifications = []
    signals = []

    candidate_score = config["vcp"]["candidate_score"]
    strong_score = config["vcp"]["strong_score"]

    for i in range(len(result)):
        row = result.iloc[i]

        vcp_result = _score_row(
            result,
            i,
        )

        score = vcp_result["score"]

        if score >= strong_score:
            classification = "strong"
        elif score >= candidate_score:
            classification = "candidate"
        else:
            classification = "none"

        trend_qualified = bool(
            row["Trend_Qualified"]
        )

        in_base = bool(
            row["In_Base"]
        )

        breakout = bool(
            row["Breakout"]
        )

        signal = classify_signal(
            score=score,
            trend_qualified=trend_qualified,
            in_base=in_base,
            breakout=breakout,
            candidate_score=candidate_score,
        )

        scores.append(score)
        classifications.append(classification)
        signals.append(signal)

    result["VCP_Score"] = scores
    result["VCP_Classification"] = classifications
    result["Signal"] = signals

    return result