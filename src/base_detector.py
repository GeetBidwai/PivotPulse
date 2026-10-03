"""Base detection for PivotPulse."""

import pandas as pd


def detect_base(
    df: pd.DataFrame,
    min_duration: int = 15,
    max_duration: int = 120,
    max_range: float = 0.30,
    max_net_decline: float = 0.15,
) -> pd.DataFrame:
    """
    Identify potential consolidation periods.

    A base must:
    - Last within the configured duration range.
    - Stay within the maximum price range.
    - Avoid an excessive net decline from the starting close.
    - Finish in the upper half of its price range.

    The detector tracks the most recent base window rather than
    independently evaluating every rolling window.
    """

    if min_duration < 1:
        raise ValueError("min_duration must be at least 1.")

    if max_duration < min_duration:
        raise ValueError(
            "max_duration must be greater than or equal to min_duration."
        )

    if max_range <= 0:
        raise ValueError("max_range must be greater than 0.")

    if not 0 <= max_net_decline <= 1:
        raise ValueError(
            "max_net_decline must be between 0 and 1."
        )

    result = df.copy()

    result["Base_Range"] = pd.NA
    result["In_Base"] = False

    if "Date" in result.columns:
        result["Base_Start"] = pd.Series(
            pd.NaT,
            index=result.index,
            dtype=result["Date"].dtype,
        )
    else:
        result["Base_Start"] = None

    base_start = None

    for i in range(len(result)):
        if base_start is None:
            if i + 1 < min_duration:
                continue

            start = i - min_duration + 1

            window_high = result.iloc[start:i + 1]["High"].max()
            window_low = result.iloc[start:i + 1]["Low"].min()

            window_range = (
                (window_high - window_low) / window_low
            )

            if window_range <= max_range:
                base_start = start
            else:
                continue

        base_duration = i - base_start + 1

        if base_duration > max_duration:
            base_start = None
            continue

        base_high = result.iloc[base_start:i + 1]["High"].max()
        base_low = result.iloc[base_start:i + 1]["Low"].min()

        base_range = (
            (base_high - base_low) / base_low
        )

        starting_close = result.iloc[base_start]["Close"]
        current_close = result.iloc[i]["Close"]

        net_decline = (
            (starting_close - current_close)
            / starting_close
        )

        range_position = (
            (current_close - base_low)
            / (base_high - base_low)
            if base_high > base_low
            else 0
        )

        if (
            base_range > max_range
            or net_decline > max_net_decline
            or range_position < 0.50
        ):
            base_start = None
            continue

        result.loc[result.index[i], "Base_Range"] = base_range
        result.loc[result.index[i], "In_Base"] = True
        result.loc[result.index[i], "Base_Start"] = (
            result.iloc[base_start]["Date"]
            if "Date" in result.columns
            else pd.NaT
        )

    result["Base_Range"] = pd.to_numeric(
        result["Base_Range"],
        errors="coerce",
    )

    return result