
"""Early-stage VCP analysis for stocks with limited trading history."""

import pandas as pd


def analyze_early_vcp(df: pd.DataFrame) -> dict:
    """
    Analyze a possible early VCP structure using limited price history.

    This is a preliminary model, not a replacement for the full VCP model.
    Its scoring rules have not been validated as probabilities of success.
    """

    if df.empty or len(df) < 30:
        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": "Not enough price history.",
        }

    data = pd.DataFrame(
        {
            "close": pd.to_numeric(df["Close"], errors="coerce"),
            "high": pd.to_numeric(df["High"], errors="coerce"),
            "low": pd.to_numeric(df["Low"], errors="coerce"),
            "volume": pd.to_numeric(df["Volume"], errors="coerce"),
        }
    ).dropna()

    if len(data) < 30:
        return {
            "signal": "NO TRADE",
            "confidence": 0,
            "reason": "Not enough valid market data.",
        }

    # 1. Current price
    current_price = float(data["close"].iloc[-1])

    # 2. Pivot: prior resistance, excluding the latest session.
    # This allows a close above previous resistance to count as a breakout.
    pivot = float(data["high"].iloc[-21:-1].max())

    # 3. Recent support
    support = float(data["low"].tail(20).min())

    # 4. Moving averages
    sma20 = float(data["close"].tail(20).mean())
    sma50 = float(data["close"].tail(min(50, len(data))).mean())

    # 5. ATR-style volatility measurement
    previous_close = data["close"].shift(1)

    true_range = pd.concat(
        [
            data["high"] - data["low"],
            (data["high"] - previous_close).abs(),
            (data["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr14 = float(true_range.rolling(14).mean().iloc[-1])
    atr_percent = (atr14 / current_price) * 100 if current_price > 0 else 0

    # 6. Volume behaviour
    recent_volume = float(data["volume"].tail(10).mean())
    prior_volume = float(data["volume"].iloc[-30:-10].mean())

    volume_contracting = (
        prior_volume > 0 and recent_volume < prior_volume
    )

    # 7. Swing-to-swing price contraction
    # Find local swing highs in the latest 30 sessions.
    # For each swing high, measure the decline to the lowest low
    # before the next swing high. Compare successive pullbacks.
    recent = data.tail(30).reset_index(drop=True)
    highs = recent["high"]
    lows = recent["low"]

    swing_highs = []

    for i in range(1, len(recent) - 1):
        is_swing_high = (
            highs.iloc[i] >= highs.iloc[i - 1]
            and highs.iloc[i] > highs.iloc[i + 1]
        )
        if is_swing_high:
            swing_highs.append(i)

    pullbacks = []

    for j in range(len(swing_highs) - 1):
        peak_index = swing_highs[j]
        next_peak_index = swing_highs[j + 1]

        peak_price = float(highs.iloc[peak_index])
        trough_price = float(
            lows.iloc[peak_index + 1 : next_peak_index + 1].min()
        )

        if peak_price > 0 and trough_price < peak_price:
            pullback_percent = (
                (peak_price - trough_price) / peak_price
            ) * 100
            pullbacks.append(pullback_percent)

    # Require at least two measurable pullbacks.
    # The latest pullback must be smaller than the previous one.
    price_contracting = (
        len(pullbacks) >= 2
        and pullbacks[-1] < pullbacks[-2]
    )

    # 8. Trend
    trend_ok = (
        current_price > sma20
        and sma20 >= sma50 * 0.97
    )

    # 9. Breakout
    breakout = current_price > pivot

    breakout_volume_ok = (
        prior_volume > 0
        and recent_volume >= prior_volume * 1.5
    )

    # 10. Score
    score = 0

    if trend_ok:
        score += 20

    if price_contracting:
        score += 20

    if volume_contracting:
        score += 15

    if atr_percent <= 5:
        score += 15

    if current_price >= pivot * 0.95:
        score += 15

    if breakout:
        score += 10

    if breakout and breakout_volume_ok:
        score += 5

    score = min(score, 100)

    # 11. Signal rules
    if breakout and breakout_volume_ok and score >= 80:
        signal = "BREAKOUT"
    elif score >= 70:
        signal = "SETUP"
    else:
        signal = "NO TRADE"

    reasons = []

    if trend_ok:
        reasons.append("trend positive")

    if price_contracting:
        reasons.append("successive swing pullbacks contracting")
    else:
        reasons.append("swing contraction not confirmed")

    if volume_contracting:
        reasons.append("volume contracting")

    if atr_percent <= 5:
        reasons.append("volatility controlled")

    if breakout:
        reasons.append("above prior resistance")

    if breakout and breakout_volume_ok:
        reasons.append("breakout volume confirmed")
    elif breakout:
        reasons.append("breakout volume not confirmed")

    return {
        "signal": signal,
        "confidence": score,
        "current_price": current_price,
        "pivot": pivot,
        "support": support,
        "sma20": sma20,
        "sma50": sma50,
        "atr_percent": atr_percent,
        "volume_contracting": bool(volume_contracting),
        "price_contracting": bool(price_contracting),
        "pullbacks_percent": pullbacks[-5:],
        "trend_ok": bool(trend_ok),
        "breakout": bool(breakout),
        "breakout_volume_ok": bool(breakout_volume_ok),
        "reason": ", ".join(reasons),
    }