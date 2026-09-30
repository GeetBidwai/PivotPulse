import pandas as pd


def add_indicators(
    df: pd.DataFrame,
    fast_sma: int = 50,
    slow_sma: int = 200,
    atr_period: int = 14,
    volume_period: int = 20,
) -> pd.DataFrame:

    result = df.copy()

    # Moving averages
    result[f"SMA_{fast_sma}"] = (
        result["Close"]
        .rolling(fast_sma)
        .mean()
    )

    result[f"SMA_{slow_sma}"] = (
        result["Close"]
        .rolling(slow_sma)
        .mean()
    )

    # 52-week high
    result["52W_High"] = (
        result["High"]
        .rolling(252)
        .max()
    )

    # Distance from 52-week high
    result["Distance_From_52W_High"] = (
        result["Close"] / result["52W_High"]
    ) - 1

    # True Range
    previous_close = result["Close"].shift(1)

    true_range = pd.concat(
        [
            result["High"] - result["Low"],
            (result["High"] - previous_close).abs(),
            (result["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    result["TR"] = true_range

    # ATR
    result[f"ATR_{atr_period}"] = (
        result["TR"]
        .rolling(atr_period)
        .mean()
    )

    # ATR as percentage of price
    result["ATR_Pct"] = (
        result[f"ATR_{atr_period}"]
        / result["Close"]
    )

    # Average volume
    result[f"AvgVolume_{volume_period}"] = (
        result["Volume"]
        .rolling(volume_period)
        .mean()
    )

    # Relative volume
    result["RelativeVolume"] = (
        result["Volume"]
        / result[f"AvgVolume_{volume_period}"]
    )

    return result