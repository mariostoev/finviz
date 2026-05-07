from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import requests
from lxml import html

from app.models.schemas import (
    AnalystTargetItem,
    FinvizMetric,
    FinvizNewsItem,
    FinvizSnapshotItem,
)
from app.services.cache import cache


FINVIZ_QUOTE_URL = "https://finviz.com/quote.ashx"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

KEY_METRICS = (
    "Price",
    "Target Price",
    "Rel Volume",
    "Avg Volume",
    "Volume",
    "Perf Week",
    "Perf Month",
    "Perf Quarter",
    "RSI (14)",
    "ATR",
    "Beta",
    "P/E",
    "EPS next Y",
    "EPS growth next Y",
)


def _fetch_quote_page(symbol: str):
    cache_key = f"finviz:quote:{symbol.upper()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    response = requests.get(
        FINVIZ_QUOTE_URL,
        params={"t": symbol.upper()},
        headers=REQUEST_HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    page = html.fromstring(response.text)
    cache.set(cache_key, page, ttl_seconds=60)
    return page


def _text_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _parse_metrics(page) -> List[FinvizMetric]:
    data = {}
    all_rows = page.cssselect("tr.table-dark-row")

    for row in all_rows:
        cells = row.cssselect("td.snapshot-td2")
        for index in range(0, len(cells) - 1, 2):
            label = cells[index].text_content().strip()
            value = cells[index + 1].text_content().strip()
            if not label:
                continue
            if label == "EPS next Y" and "EPS next Y" in data:
                data["EPS growth next Y"] = value
                continue
            if label == "Volatility":
                volatility = value.split()
                if volatility:
                    data["Volatility (Week)"] = volatility[0]
                    data["Volatility (Month)"] = volatility[-1]
                continue
            data[label] = value

    metrics: List[FinvizMetric] = []
    for label in KEY_METRICS:
        value = data.get(label)
        if value:
            metrics.append(FinvizMetric(label=label, value=value))

    for label in ("Volatility (Week)", "Volatility (Month)"):
        value = data.get(label)
        if value:
            metrics.append(FinvizMetric(label=label, value=value))

    return metrics


def _parse_news_timestamp(raw_timestamp: str, current_date) -> Optional[datetime]:
    raw = raw_timestamp.strip()
    if not raw:
        return None

    if "Today" in raw:
        time_part = raw.replace("Today", "").strip()
        parsed_time = datetime.strptime(time_part, "%I:%M%p")
        return datetime.combine(datetime.now().date(), parsed_time.time())

    if len(raw) > 8 and "-" in raw:
        for fmt in ("%b-%d-%y %I:%M%p", "%b-%d-%Y %I:%M%p"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    parsed_time = datetime.strptime(raw, "%I:%M%p")
    return datetime.combine(current_date, parsed_time.time())


def _parse_news(page, limit: int = 6) -> List[FinvizNewsItem]:
    tables = page.cssselect("table#news-table")
    if not tables:
        return []

    rows = tables[0].cssselect("tr")
    items: List[FinvizNewsItem] = []
    current_date = datetime.now().date()

    for row in rows:
        cells = row.cssselect("td")
        if len(cells) < 2:
            continue
        try:
            parsed_timestamp = _parse_news_timestamp(cells[0].text_content(), current_date)
        except ValueError:
            continue
        if parsed_timestamp is None:
            continue
        current_date = parsed_timestamp.date()

        link = cells[1].cssselect("a.tab-link-news")
        if not link:
            continue
        source = None
        source_nodes = cells[1].cssselect("div.news-link-right span")
        if source_nodes:
            source = source_nodes[0].text_content().strip().strip("()")

        items.append(
            FinvizNewsItem(
                timestamp=parsed_timestamp.strftime("%Y-%m-%d %H:%M"),
                headline=link[0].text_content().strip(),
                url=_text_or_none(link[0].get("href")),
                source=_text_or_none(source),
            )
        )
        if len(items) >= limit:
            break

    return items


def _parse_targets(page, limit: int = 5) -> List[AnalystTargetItem]:
    tables = page.cssselect("table.js-table-ratings") or page.cssselect(
        "table.fullview-ratings-outer"
    )
    if not tables:
        return []

    rows = tables[0].cssselect("tbody tr") or tables[0].cssselect("tr")
    items: List[AnalystTargetItem] = []

    for row in rows:
        cells = [cell.text_content().strip() for cell in row.cssselect("td")]
        cells = [value.replace("→", "->").replace("$", "") for value in cells if value]
        if len(cells) < 4:
            continue

        parsed_date = None
        for fmt in ("%b-%d-%y", "%b-%d-%Y"):
            try:
                parsed_date = datetime.strptime(cells[0], fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
        if parsed_date is None:
            continue

        item = AnalystTargetItem(
            date=parsed_date,
            category=cells[1],
            analyst=cells[2],
            rating=cells[3],
        )

        if len(cells) >= 5 and cells[4]:
            price_value = cells[4].replace(" ", "")
            if "->" in price_value:
                left, right = price_value.split("->", 1)
                try:
                    item.target_from = float(left) if left else None
                except ValueError:
                    item.target_from = None
                try:
                    item.target_to = float(right) if right else None
                except ValueError:
                    item.target_to = None
            else:
                try:
                    item.target = float(price_value)
                except ValueError:
                    item.target = None

        items.append(item)
        if len(items) >= limit:
            break

    return items


def get_finviz_snapshot(symbol: str) -> FinvizSnapshotItem:
    page = _fetch_quote_page(symbol)

    ticker_nodes = page.cssselect("h1.quote-header_ticker-wrapper_ticker")
    resolved_symbol = ticker_nodes[0].text_content().strip() if ticker_nodes else symbol.upper()

    company = None
    website = None
    company_nodes = page.cssselect("h2.quote-header_ticker-wrapper_company a.tab-link")
    if company_nodes:
        company = _text_or_none(company_nodes[0].text_content())
        link = company_nodes[0].attrib.get("href", "")
        website = link if link.startswith("http") else None

    sector = None
    industry = None
    quote_links = []
    for link in page.cssselect("div.quote-links a.tab-link"):
        href = link.attrib.get("href", "")
        if "f=sec_" in href or "f=ind_" in href:
            quote_links.append(link.text_content().strip())
    if quote_links:
        sector = quote_links[0] if len(quote_links) > 0 else None
        industry = quote_links[1] if len(quote_links) > 1 else None

    return FinvizSnapshotItem(
        symbol=resolved_symbol,
        company=company,
        sector=sector,
        industry=industry,
        website=website,
        metrics=_parse_metrics(page),
        news=_parse_news(page),
        analyst_targets=_parse_targets(page),
    )
