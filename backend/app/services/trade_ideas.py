from __future__ import annotations

import os
from typing import Iterable, List, Optional, Tuple

from app.models.schemas import FinvizMetric, TradeIdeaItem, TradeIdeasResponse
from app.services.analysis import _bounded_int
from app.services.finviz_data import get_finviz_snapshot
from app.services.indicators import rsi, sma, trend_from_mas
from app.services.market_data import fetch_price_series
from app.services.news_sentiment import fetch_news_and_sentiment

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - keep optional dependency non-fatal
    OpenAI = None


DATA_NOTICE = (
    "Finviz quote data is delayed and this scanner is for research only. "
    "It should not be treated as live execution advice."
)


def _metric_value(metrics: Iterable[FinvizMetric], label: str) -> Optional[str]:
    for metric in metrics:
        if metric.label == label:
            return metric.value
    return None


def _as_float(raw: Optional[str]) -> Optional[float]:
    if raw is None:
        return None
    cleaned = (
        raw.replace("%", "")
        .replace(",", "")
        .replace("$", "")
        .replace("B", "")
        .replace("M", "")
        .replace("K", "")
        .strip()
    )
    try:
        return float(cleaned)
    except ValueError:
        return None


def _pick_target_price(snapshot) -> Optional[float]:
    metric_target = _as_float(_metric_value(snapshot.metrics, "Target Price"))
    if metric_target is not None:
        return metric_target

    for item in snapshot.analyst_targets:
        if item.target_to is not None:
            return item.target_to
        if item.target is not None:
            return item.target
    return None


def _direction_and_score(
    current_price: Optional[float],
    ma50: Optional[float],
    ma200: Optional[float],
    rsi_value: Optional[float],
    sentiment_score: float,
    target_delta_pct: Optional[float],
) -> Tuple[str, int, List[str]]:
    score = 35
    risks: List[str] = []

    bullish_stack = (
        current_price is not None
        and ma50 is not None
        and ma200 is not None
        and current_price > ma50 > ma200
    )
    bearish_stack = (
        current_price is not None
        and ma50 is not None
        and ma200 is not None
        and current_price < ma50 < ma200
    )

    if bullish_stack:
        score += 22
    elif bearish_stack:
        score += 22
    else:
        risks.append("Trend stack is mixed across price, MA50, and MA200.")

    if rsi_value is not None:
        if 48 <= rsi_value <= 67:
            score += 10
        elif 33 <= rsi_value <= 52:
            score += 6
        elif rsi_value > 72:
            risks.append("RSI is stretched above 72, which can mean chase risk.")
        elif rsi_value < 28:
            risks.append("RSI is below 28, which can mean falling-knife risk.")
    else:
        risks.append("RSI could not be computed from the selected timeframe.")

    if sentiment_score > 0.15:
        score += 10
    elif sentiment_score < -0.15:
        score += 10
    else:
        risks.append("Headline sentiment is mixed or weak.")

    if target_delta_pct is not None:
        if target_delta_pct >= 8:
            score += 18
        elif target_delta_pct <= -8:
            score += 18
        elif abs(target_delta_pct) < 3:
            risks.append("Analyst target is close to spot, so upside/downside is limited.")
    else:
        risks.append("No usable analyst target was found.")

    if bullish_stack and sentiment_score >= 0:
        return "long", score, risks
    if bearish_stack and sentiment_score <= 0:
        return "short", score, risks
    if bullish_stack:
        return "long", score - 5, risks
    if bearish_stack:
        return "short", score - 5, risks
    return "watchlist", score - 10, risks


def _build_setup(direction: str, trend: str, target_delta_pct: Optional[float]) -> Tuple[str, str]:
    if direction == "long":
        setup = "Momentum continuation long"
        rationale = "Trend structure favors strength and the scanner sees a possible upside continuation setup."
    elif direction == "short":
        setup = "Breakdown continuation short"
        rationale = "Trend structure favors weakness and the scanner sees a possible downside continuation setup."
    else:
        setup = "Watchlist only"
        rationale = "The data stack is mixed, so this name is better treated as a watchlist candidate than an active setup."

    if target_delta_pct is not None:
        rationale += f" Analyst target gap is {target_delta_pct:.1f}% versus spot."
    rationale += f" Trend is currently {trend}."
    return setup, rationale


def _build_ai_summary(
    symbol: str,
    direction: str,
    trend: str,
    rsi_value: Optional[float],
    sentiment_label: str,
    target_delta_pct: Optional[float],
    risks: List[str],
) -> str:
    summary = f"{symbol} screens as a {direction} idea with a {trend} trend"
    if rsi_value is not None:
        summary += f", RSI {rsi_value:.1f}"
    summary += f", and {sentiment_label} headlines"
    if target_delta_pct is not None:
        summary += f". Analyst gap: {target_delta_pct:.1f}%."
    else:
        summary += "."
    if risks:
        summary += f" Main risk: {risks[0]}"
    return summary


def _maybe_generate_llm_summary(items: List[TradeIdeaItem]) -> Tuple[str, Optional[str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model or OpenAI is None or not items:
        return "rules", None

    prompt_lines = [
        "Summarize these trade ideas for a human trader.",
        "Be concise, cautious, and explicitly mention that the data is delayed and not execution-grade.",
        "Rank strongest ideas first and call out the biggest common risk.",
        "",
    ]
    for item in items[:5]:
        prompt_lines.append(
            (
                f"{item.symbol}: direction={item.direction}, score={item.score}, "
                f"trend={item.trend}, rsi={item.rsi_14}, sentiment={item.sentiment_label}, "
                f"target_delta_pct={item.analyst_target_delta_pct}, setup={item.setup}, "
                f"risks={'; '.join(item.risks[:2]) or 'none'}"
            )
        )

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(model=model, input="\n".join(prompt_lines))
        return "rules+openai", response.output_text.strip() or None
    except Exception:
        return "rules", None


def build_trade_ideas(symbols: List[str], timeframe: str = "1d") -> TradeIdeasResponse:
    items: List[TradeIdeaItem] = []

    for symbol in symbols:
        snapshot = get_finviz_snapshot(symbol)
        market_points = fetch_price_series(symbol, "stock", timeframe=timeframe)
        closes = [point["close"] for point in market_points]
        current_price = closes[-1] if closes else None
        ma50 = sma(closes, 50)
        ma200 = sma(closes, 200)
        trend = trend_from_mas(ma50, ma200)
        rsi_value = rsi(closes, 14)
        _, sentiment_score, sentiment_label = fetch_news_and_sentiment(symbol, "stock")
        target_price = _pick_target_price(snapshot)
        target_delta_pct = None
        if current_price and target_price:
            target_delta_pct = ((target_price - current_price) / current_price) * 100.0

        direction, raw_score, risks = _direction_and_score(
            current_price=current_price,
            ma50=ma50,
            ma200=ma200,
            rsi_value=rsi_value,
            sentiment_score=sentiment_score,
            target_delta_pct=target_delta_pct,
        )
        score = _bounded_int(raw_score)
        confidence = _bounded_int(score * 0.9 if direction != "watchlist" else score * 0.75)
        setup, rationale = _build_setup(direction, trend, target_delta_pct)
        ai_summary = _build_ai_summary(
            symbol=snapshot.symbol,
            direction=direction,
            trend=trend,
            rsi_value=rsi_value,
            sentiment_label=sentiment_label,
            target_delta_pct=target_delta_pct,
            risks=risks,
        )

        items.append(
            TradeIdeaItem(
                symbol=snapshot.symbol,
                company=snapshot.company,
                direction=direction,
                score=score,
                confidence=confidence,
                current_price=current_price,
                trend=trend,
                rsi_14=rsi_value,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                analyst_target_price=target_price,
                analyst_target_delta_pct=target_delta_pct,
                setup=setup,
                rationale=rationale,
                ai_summary=ai_summary,
                risks=risks[:3],
                finviz_metrics=snapshot.metrics,
                latest_news=snapshot.news[:3],
            )
        )

    items.sort(key=lambda item: (item.score, item.confidence), reverse=True)
    generated_by, llm_summary = _maybe_generate_llm_summary(items)
    return TradeIdeasResponse(
        items=items,
        llm_summary=llm_summary,
        generated_by=generated_by,
        data_notice=DATA_NOTICE,
    )
