"""Tests for VCP scoring."""


from src.vcp_score import score_vcp


def test_strong_vcp_score():
    """Verify that tightening contractions produce a strong score."""

    result = score_vcp(
        [0.18, 0.12, 0.08, 0.06],
        final_contraction_max_depth=0.10,
    )

    assert result["score"] >= 80
    assert result["tightening_score"] == 30
    assert result["final_contraction_score"] == 40


def test_insufficient_contractions():
    """Verify that fewer than two contractions produces zero score."""

    result = score_vcp([0.10])

    assert result["score"] == 0