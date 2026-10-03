"""Tests for VCP scoring."""


from src.vcp_score import score_vcp


def test_score_vcp():
    """Verify VCP scoring returns a valid score."""

    result = score_vcp(
        contraction_depths=[0.20, 0.12, 0.08],
        final_contraction_max_depth=0.10,
    )

    assert 0 <= result["score"] <= 100
    assert result["contraction_score"] > 0
    assert result["tightening_score"] > 0
    assert result["final_contraction_score"] > 0


def test_rejects_too_few_contractions():
    """Verify fewer than the minimum contractions are rejected."""

    result = score_vcp(
        contraction_depths=[0.08],
        min_contractions=2,
        max_contractions=4,
    )

    assert result["score"] == 0


def test_rejects_too_many_contractions():
    """Verify more than the maximum contractions are rejected."""

    result = score_vcp(
        contraction_depths=[0.20, 0.15, 0.12, 0.09, 0.07],
        min_contractions=2,
        max_contractions=4,
    )

    assert result["score"] == 0