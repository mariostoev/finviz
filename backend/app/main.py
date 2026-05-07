import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    AnalysisItem,
    AnalysisResponse,
    AssetList,
    Asset,
    AssetNewsItem,
    FinvizSnapshotResponse,
    IndicatorSet,
    MarketDataItem,
    MarketDataResponse,
    NewsResponse,
    TradeIdeasResponse,
)
from app.services.analysis import build_bias
from app.services.asset_store import asset_store
from app.services.finviz_data import get_finviz_snapshot
from app.services.indicators import rsi, sma, trend_from_mas
from app.services.market_data import fetch_price_series
from app.services.news_sentiment import fetch_news_and_sentiment
from app.services.trade_ideas import build_trade_ideas

app = FastAPI(title="Market Bias API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/assets", response_model=AssetList)
def list_assets() -> AssetList:
    return AssetList(assets=asset_store.list())


@app.post("/assets", response_model=AssetList)
def add_asset(asset: Asset) -> AssetList:
    asset_store.add(asset)
    return AssetList(assets=asset_store.list())


@app.delete("/assets/{symbol}", response_model=AssetList)
def remove_asset(symbol: str) -> AssetList:
    removed = asset_store.remove(symbol)
    if not removed:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetList(assets=asset_store.list())


@app.get("/market-data", response_model=MarketDataResponse)
def get_market_data(timeframe: str = Query(default="1d")) -> MarketDataResponse:
    items = []
    for asset in asset_store.list():
        points = fetch_price_series(asset.symbol, asset.type, timeframe=timeframe)
        closes = [p["close"] for p in points]
        ma50 = sma(closes, 50)
        ma200 = sma(closes, 200)
        trend = trend_from_mas(ma50, ma200)
        indicators = IndicatorSet(
            rsi_14=rsi(closes, 14),
            ma_50=ma50,
            ma_200=ma200,
            trend=trend,
        )
        items.append(
            MarketDataItem(
                symbol=asset.symbol,
                type=asset.type,
                current_price=(closes[-1] if closes else None),
                timeframe=timeframe,
                series=points,
                indicators=indicators,
            )
        )

    return MarketDataResponse(items=items)


@app.get("/news", response_model=NewsResponse)
def get_news() -> NewsResponse:
    items = []
    for asset in asset_store.list():
        headlines, score, label = fetch_news_and_sentiment(asset.symbol, asset.type)
        items.append(
            AssetNewsItem(
                symbol=asset.symbol,
                headlines=headlines,
                sentiment_label=label,
                sentiment_score=score,
            )
        )
    return NewsResponse(items=items)


@app.get("/analysis", response_model=AnalysisResponse)
def get_analysis(timeframe: str = Query(default="1d")) -> AnalysisResponse:
    result = []
    for asset in asset_store.list():
        points = fetch_price_series(asset.symbol, asset.type, timeframe=timeframe)
        closes = [p["close"] for p in points]
        current = closes[-1] if closes else None
        ma50 = sma(closes, 50)
        ma200 = sma(closes, 200)
        trend = trend_from_mas(ma50, ma200)
        rsi_value = rsi(closes, 14)
        _, score, label = fetch_news_and_sentiment(asset.symbol, asset.type)
        bias, confidence, explanation = build_bias(current, ma50, ma200, score)

        result.append(
            AnalysisItem(
                symbol=asset.symbol,
                current_price=current,
                rsi_14=rsi_value,
                trend=trend,
                sentiment_score=score,
                sentiment_label=label,
                bias=bias,
                confidence=confidence,
                explanation=explanation,
            )
        )
    return AnalysisResponse(items=result)


@app.get("/finviz-snapshot", response_model=FinvizSnapshotResponse)
def get_finviz_data() -> FinvizSnapshotResponse:
    items = []
    for asset in asset_store.list():
        if asset.type != "stock":
            continue
        try:
            items.append(get_finviz_snapshot(asset.symbol))
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to load Finviz snapshot for {asset.symbol}: {exc}",
            ) from exc
    return FinvizSnapshotResponse(items=items)


@app.get("/trade-ideas", response_model=TradeIdeasResponse)
def get_trade_ideas(timeframe: str = Query(default="1d")) -> TradeIdeasResponse:
    stock_symbols = [asset.symbol for asset in asset_store.list() if asset.type == "stock"]
    if not stock_symbols:
        return build_trade_ideas([], timeframe=timeframe)
    try:
        return build_trade_ideas(stock_symbols, timeframe=timeframe)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Trade scanner failed: {exc}") from exc


@app.get("/health")
def health() -> dict:
    return {"ok": True}
