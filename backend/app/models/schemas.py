from typing import List, Literal, Optional

from pydantic import BaseModel, Field


AssetType = Literal["stock", "forex"]
BiasType = Literal["bullish", "bearish", "neutral"]
TrendType = Literal["bullish", "bearish", "neutral"]
SentimentLabel = Literal["positive", "negative", "neutral"]
TradeDirection = Literal["long", "short", "watchlist"]


class Asset(BaseModel):
    symbol: str = Field(..., description="Asset symbol, e.g. AAPL or EUR/USD")
    type: AssetType


class AssetList(BaseModel):
    assets: List[Asset]


class OHLCPoint(BaseModel):
    timestamp: str
    close: float


class IndicatorSet(BaseModel):
    rsi_14: Optional[float]
    ma_50: Optional[float]
    ma_200: Optional[float]
    trend: TrendType


class MarketDataItem(BaseModel):
    symbol: str
    type: AssetType
    current_price: Optional[float]
    timeframe: str
    series: List[OHLCPoint]
    indicators: IndicatorSet


class MarketDataResponse(BaseModel):
    items: List[MarketDataItem]


class NewsHeadline(BaseModel):
    title: str
    link: Optional[str] = None
    publisher: Optional[str] = None


class AssetNewsItem(BaseModel):
    symbol: str
    headlines: List[NewsHeadline]
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)


class NewsResponse(BaseModel):
    items: List[AssetNewsItem]


class AnalysisItem(BaseModel):
    symbol: str
    current_price: Optional[float]
    rsi_14: Optional[float]
    trend: TrendType
    sentiment_score: float
    sentiment_label: SentimentLabel
    bias: BiasType
    confidence: int = Field(..., ge=0, le=100)
    explanation: str


class AnalysisResponse(BaseModel):
    items: List[AnalysisItem]


class FinvizMetric(BaseModel):
    label: str
    value: str


class FinvizNewsItem(BaseModel):
    timestamp: str
    headline: str
    url: Optional[str] = None
    source: Optional[str] = None


class AnalystTargetItem(BaseModel):
    date: str
    category: str
    analyst: str
    rating: str
    target_from: Optional[float] = None
    target_to: Optional[float] = None
    target: Optional[float] = None


class FinvizSnapshotItem(BaseModel):
    symbol: str
    company: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    metrics: List[FinvizMetric]
    news: List[FinvizNewsItem]
    analyst_targets: List[AnalystTargetItem]


class FinvizSnapshotResponse(BaseModel):
    items: List[FinvizSnapshotItem]


class TradeIdeaItem(BaseModel):
    symbol: str
    company: Optional[str] = None
    direction: TradeDirection
    score: int = Field(..., ge=0, le=100)
    confidence: int = Field(..., ge=0, le=100)
    current_price: Optional[float] = None
    trend: TrendType
    rsi_14: Optional[float] = None
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: SentimentLabel
    analyst_target_price: Optional[float] = None
    analyst_target_delta_pct: Optional[float] = None
    setup: str
    rationale: str
    ai_summary: str
    risks: List[str]
    finviz_metrics: List[FinvizMetric]
    latest_news: List[FinvizNewsItem]


class TradeIdeasResponse(BaseModel):
    items: List[TradeIdeaItem]
    llm_summary: Optional[str] = None
    generated_by: str
    data_notice: str
