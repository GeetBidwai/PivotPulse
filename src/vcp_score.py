"""VCP scoring logic for PivotPulse."""


def score_vcp(
    contraction_depths: list[float],
    final_contraction_max_depth: float = 0.10,
    min_contractions: int = 2,
    max_contractions: int = 4,
    atr_pcts: list[float] | None = None,
    relative_volumes: list[float] | None = None,
) -> dict:
    """
    Calculate an explainable VCP score from contraction structure,
    volatility, and volume behavior.

    Returns a score from 0 to 100 plus individual components.
    """

    contraction_count = len(contraction_depths)

    if (
        contraction_count < min_contractions
        or contraction_count > max_contractions
    ):
        return {
            "score": 0,
            "contraction_score": 0,
            "tightening_score": 0,
            "final_contraction_score": 0,
            "volatility_score": 0,
            "volume_score": 0,
        }

    contraction_score = min(
        contraction_count / max_contractions,
        1.0,
    ) * 25

    tightening_pairs = sum(
        current <= previous
        for previous, current in zip(
            contraction_depths,
            contraction_depths[1:],
        )
    )

    total_pairs = contraction_count - 1

    tightening_score = (
        tightening_pairs / total_pairs
    ) * 25

    final_depth = contraction_depths[-1]

    if final_depth <= final_contraction_max_depth:
        final_contraction_score = 35
    else:
        final_contraction_score = max(
            0,
            35 * (
                1
                - (
                    final_depth
                    - final_contraction_max_depth
                )
            ),
        )

    volatility_score = 0

    if atr_pcts and len(atr_pcts) >= 2:
        atr_midpoint = len(atr_pcts) // 2

        first_half_atr = sum(
            atr_pcts[:atr_midpoint]
        ) / atr_midpoint

        second_half_atr = sum(
            atr_pcts[atr_midpoint:]
        ) / len(atr_pcts[atr_midpoint:])

        if second_half_atr <= first_half_atr:
            volatility_score = 7.5

    volume_score = 0

    if relative_volumes and len(relative_volumes) >= 2:
        volume_midpoint = len(relative_volumes) // 2

        first_half_volume = sum(
            relative_volumes[:volume_midpoint]
        ) / volume_midpoint

        second_half_volume = sum(
            relative_volumes[volume_midpoint:]
        ) / len(relative_volumes[volume_midpoint:])

        if second_half_volume <= first_half_volume:
            volume_score = 7.5

    score = round(
        contraction_score
        + tightening_score
        + final_contraction_score
        + volatility_score
        + volume_score
    )

    return {
        "score": min(score, 100),
        "contraction_score": round(contraction_score),
        "tightening_score": round(tightening_score),
        "final_contraction_score": round(
            final_contraction_score
        ),
        "volatility_score": volatility_score,
        "volume_score": volume_score,
    }