from typing import List, Tuple

import yfinance as yf

from app.models.schemas import NewsHeadline
from app.services.cache import cache
from app.services.market_data import normalize_symbol


POSITIVE_WORDS = {
    "beat",
    "growth",
    "surge",
    "up",
    "bullish",
    "record",
    "profit",
    "optimistic",
    "strong",
    "gain",
}

NEGATIVE_WORDS = {
    "miss",
    "drop",
    "down",
    "bearish",
    "loss",
    "lawsuit",
    "weak",
    "risk",
    "cuts",
    "decline",
}


def _score_text(text: str) -> float:
    words = text.lower().split()
    if not words:
        return 0.0
    pos = sum(1 for w in words if w.strip(".,:;!?") in POSITIVE_WORDS)
    neg = sum(1 for w in words if w.strip(".,:;!?") in NEGATIVE_WORDS)
    raw = (pos - neg) / max(len(words), 1)
    # Scale slightly so typical scores are not near zero.
    return max(-1.0, min(1.0, raw * 6))


def sentiment_from_score(score: float) -> str:
    if score > 0.12:
        return "positive"
    if score < -0.12:
        return "negative"
    return "neutral"


def fetch_news_and_sentiment(symbol: str, asset_type: str, limit: int = 5) -> Tuple[List[NewsHeadline], float, str]:
    resolved_symbol = normalize_symbol(symbol, asset_type)
    cache_key = f"news:{resolved_symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    headlines: List[NewsHeadline] = []
    scores: List[float] = []
    try:
        ticker = yf.Ticker(resolved_symbol)
        raw_news = ticker.news or []
        for item in raw_news[:limit]:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            link = item.get("link")
            publisher = item.get("publisher")
            headlines.append(NewsHeadline(title=title, link=link, publisher=publisher))
            scores.append(_score_text(title))
    except Exception:
        # Keep service resilient if provider errors/rate-limits.
        pass

    final_score = 0.0 if not scores else sum(scores) / len(scores)
    label = sentiment_from_score(final_score)
    payload = (headlines, final_score, label)
    cache.set(cache_key, payload, ttl_seconds=120)
    return payload
