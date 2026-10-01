"""Utilities for securely loading Upstox credentials."""

import os

from dotenv import load_dotenv


load_dotenv()


def get_upstox_access_token() -> str:
    """Return the Upstox access token from the environment."""

    token = os.getenv("UPSTOX_ACCESS_TOKEN")

    if not token:
        raise RuntimeError(
            "UPSTOX_ACCESS_TOKEN is not set. "
            "Check your .env file."
        )

    return token