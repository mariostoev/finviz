from typing import Dict, List, Tuple

import yfinance as yf

from app.services.cache import cache


TIMEFRAME_MAP: Dict[str, Tuple[str, str, int]] = {
    "1m": ("1d", "1m", 30),
    "5m": ("5d", "5m", 45),
    "1h": ("1mo", "1h", 90),
    "1d": ("1y", "1d", 300),
}


def normalize_symbol(symbol: str, asset_type: str) -> str:
    if asset_type == "forex":
        compact = symbol.replace("/", "").upper()
        return f"{compact}=X"
    return symbol.upper()


def fetch_price_series(symbol: str, asset_type: str, timeframe: str) -> List[dict]:
    if timeframe not in TIMEFRAME_MAP:
        timeframe = "1d"
    period, interval, ttl = TIMEFRAME_MAP[timeframe]
    resolved_symbol = normalize_symbol(symbol, asset_type)
    cache_key = f"prices:{resolved_symbol}:{timeframe}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    ticker = yf.Ticker(resolved_symbol)
    hist = ticker.history(period=period, interval=interval, auto_adjust=False)

    points: List[dict] = []
    if not hist.empty:
        for idx, row in hist.iterrows():
            close = row.get("Close")
            if close is None:
                continue
            points.append(
                {
                    "timestamp": idx.isoformat(),
                    "close": float(close),
                }
            )

    cache.set(cache_key, points, ttl_seconds=ttl)
    return points
