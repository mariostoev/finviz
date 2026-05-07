from typing import Optional, Tuple


def _bounded_int(value: float) -> int:
    return max(0, min(100, int(round(value))))


def build_bias(
    current_price: Optional[float],
    ma50: Optional[float],
    ma200: Optional[float],
    sentiment_score: float,
) -> Tuple[str, int, str]:
    bullish_price = (
        current_price is not None
        and ma50 is not None
        and ma200 is not None
        and current_price > ma50 > ma200
    )
    bearish_price = (
        current_price is not None
        and ma50 is not None
        and ma200 is not None
        and current_price < ma50 < ma200
    )

    if bullish_price and sentiment_score > 0.05:
        confidence = _bounded_int(60 + min(sentiment_score, 1.0) * 35)
        return "bullish", confidence, "Uptrend + positive news sentiment"

    if bearish_price and sentiment_score < -0.05:
        confidence = _bounded_int(60 + min(abs(sentiment_score), 1.0) * 35)
        return "bearish", confidence, "Downtrend + negative news sentiment"

    if bullish_price:
        return "bullish", 55, "Uptrend in price structure, mixed sentiment"

    if bearish_price:
        return "bearish", 55, "Downtrend in price structure, mixed sentiment"

    if sentiment_score > 0.25:
        return "bullish", 45, "Mixed trend but notably positive sentiment"

    if sentiment_score < -0.25:
        return "bearish", 45, "Mixed trend but notably negative sentiment"

    return "neutral", 35, "Trend and sentiment are mixed/unclear"
