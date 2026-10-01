"""VCP scoring logic for PivotPulse."""

import pandas as pd


def score_vcp(
    contraction_depths: list[float],
    final_contraction_max_depth: float = 0.10,
) -> dict:
    """
    Calculate an explainable VCP score from contraction depths.

    Returns a score from 0 to 100 plus the individual components.
    """

    if len(contraction_depths) < 2:
        return {
            "score": 0,
            "contraction_score": 0,
            "tightening_score": 0,
            "final_contraction_score": 0,
        }

    contraction_score = min(
        len(contraction_depths) / 4,
        1.0,
    ) * 30

    tightening_pairs = 0

    for previous, current in zip(
        contraction_depths,
        contraction_depths[1:],
    ):
        if current <= previous:
            tightening_pairs += 1

    total_pairs = len(contraction_depths) - 1

    tightening_score = (
        tightening_pairs / total_pairs
    ) * 30

    final_depth = contraction_depths[-1]

    if final_depth <= final_contraction_max_depth:
        final_contraction_score = 40
    else:
        final_contraction_score = max(
            0,
            40
            * (
                1
                - (
                    final_depth
                    - final_contraction_max_depth
                )
            ),
        )

    score = round(
        contraction_score
        + tightening_score
        + final_contraction_score
    )

    return {
        "score": min(score, 100),
        "contraction_score": round(contraction_score),
        "tightening_score": round(tightening_score),
        "final_contraction_score": round(
            final_contraction_score
        ),
    }