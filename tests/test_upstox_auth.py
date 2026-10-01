"""Tests for Upstox authentication utilities."""

from src.data.upstox_auth import get_upstox_access_token


def test_upstox_access_token_is_available():
    """Verify that the Upstox access token can be loaded."""

    token = get_upstox_access_token()

    assert token
    assert isinstance(token, str)