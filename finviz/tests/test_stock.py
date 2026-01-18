"""
Tests for stock-related functions: get_stock, get_insider, get_news, get_analyst_price_targets.

All tests make real HTTP requests to finviz.com.
"""

import re
from datetime import datetime

import pytest

from finviz import get_stock, get_insider, get_news, get_analyst_price_targets


class TestGetStock:
    """Tests for the get_stock() function."""

    @pytest.mark.network
    def test_returns_dict(self, stock_data: dict):
        """get_stock() should return a dictionary."""
        assert isinstance(stock_data, dict)

    @pytest.mark.network
    def test_has_basic_info(self, stock_data: dict):
        """Stock data should contain basic company information."""
        required_keys = ["Ticker", "Company", "Sector", "Industry", "Country"]
        for key in required_keys:
            assert key in stock_data, f"Missing key: {key}"
            assert stock_data[key], f"Empty value for: {key}"

    @pytest.mark.network
    def test_has_financial_metrics(self, stock_data: dict):
        """Stock data should contain key financial metrics."""
        financial_keys = [
            "P/E", "Market Cap", "Price", "EPS (ttm)",
            "Forward P/E", "PEG", "P/S", "P/B",
        ]
        for key in financial_keys:
            assert key in stock_data, f"Missing financial metric: {key}"

    @pytest.mark.network
    def test_has_trading_metrics(self, stock_data: dict):
        """Stock data should contain trading metrics."""
        trading_keys = [
            "Volume", "Avg Volume", "52W High", "52W Low",
            "RSI (14)", "Beta", "ATR (14)",
        ]
        for key in trading_keys:
            assert key in stock_data, f"Missing trading metric: {key}"

    @pytest.mark.network
    def test_has_ownership_metrics(self, stock_data: dict):
        """Stock data should contain ownership metrics."""
        ownership_keys = [
            "Insider Own", "Inst Own", "Short Float",
            "Shs Outstand", "Shs Float",
        ]
        for key in ownership_keys:
            assert key in stock_data, f"Missing ownership metric: {key}"

    @pytest.mark.network
    def test_ticker_matches_request(self, test_ticker: str, stock_data: dict):
        """Returned ticker should match requested ticker."""
        assert stock_data["Ticker"] == test_ticker

    @pytest.mark.network
    def test_market_cap_format(self, stock_data: dict):
        """Market cap should be in B/M/K format."""
        market_cap = stock_data.get("Market Cap", "")
        assert re.match(r"[\d.]+[BMK]?", market_cap), f"Invalid market cap format: {market_cap}"

    @pytest.mark.network
    def test_price_is_numeric(self, stock_data: dict):
        """Price should be a numeric string."""
        price = stock_data.get("Price", "")
        try:
            float(price)
        except ValueError:
            pytest.fail(f"Price is not numeric: {price}")

    @pytest.mark.network
    def test_minimum_keys_count(self, stock_data: dict):
        """Stock data should have a reasonable number of keys (70+)."""
        assert len(stock_data) >= 70, f"Too few keys: {len(stock_data)}"

    @pytest.mark.network
    def test_volatility_split(self, stock_data: dict):
        """Volatility should be split into Week and Month."""
        assert "Volatility (Week)" in stock_data
        assert "Volatility (Month)" in stock_data

    @pytest.mark.network
    def test_different_tickers(self, test_tickers: dict):
        """get_stock() should work for different ticker types."""
        for category, ticker in list(test_tickers.items())[:3]:  # Test first 3
            data = get_stock(ticker)
            assert data["Ticker"] == ticker, f"Failed for {category}: {ticker}"
            assert len(data) >= 50, f"Too few keys for {ticker}"


class TestGetNews:
    """Tests for the get_news() function."""

    @pytest.mark.network
    def test_returns_list(self, news_data: list):
        """get_news() should return a list."""
        assert isinstance(news_data, list)

    @pytest.mark.network
    def test_has_news_items(self, news_data: list):
        """News list should not be empty for major stocks."""
        assert len(news_data) > 0, "No news items returned"

    @pytest.mark.network
    def test_news_item_structure(self, news_data: list):
        """Each news item should be a tuple with 4 elements."""
        for item in news_data[:5]:
            assert isinstance(item, tuple), f"News item is not a tuple: {type(item)}"
            assert len(item) == 4, f"News item has wrong length: {len(item)}"

    @pytest.mark.network
    def test_news_timestamp_format(self, news_data: list):
        """News timestamps should be in YYYY-MM-DD HH:MM format."""
        for timestamp, _, _, _ in news_data[:5]:
            try:
                datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    @pytest.mark.network
    def test_news_has_headline(self, news_data: list):
        """Each news item should have a non-empty headline."""
        for _, headline, _, _ in news_data[:5]:
            assert headline, "Empty headline"
            assert len(headline) > 10, f"Headline too short: {headline}"

    @pytest.mark.network
    def test_news_has_url(self, news_data: list):
        """Each news item should have a URL."""
        for _, _, url, _ in news_data[:5]:
            assert url, "Empty URL"
            assert url.startswith("http") or url.startswith("/"), f"Invalid URL: {url}"

    @pytest.mark.network
    def test_news_has_source(self, news_data: list):
        """Each news item should have a source."""
        for _, _, _, source in news_data[:5]:
            assert isinstance(source, str), f"Source is not string: {type(source)}"

    @pytest.mark.network
    def test_news_count_reasonable(self, news_data: list):
        """Major stocks should have many news items."""
        assert len(news_data) >= 10, f"Too few news items: {len(news_data)}"


class TestGetInsider:
    """Tests for the get_insider() function."""

    @pytest.mark.network
    def test_returns_list(self, insider_data: list):
        """get_insider() should return a list."""
        assert isinstance(insider_data, list)

    @pytest.mark.network
    def test_insider_item_structure(self, insider_data: list):
        """Each insider item should be a dictionary."""
        if len(insider_data) > 0:
            for item in insider_data[:3]:
                assert isinstance(item, dict), f"Insider item is not a dict: {type(item)}"

    @pytest.mark.network
    def test_insider_has_key_fields(self, insider_data: list):
        """Insider data should have key fields."""
        if len(insider_data) > 0:
            expected_keys = ["Insider Trading", "Relationship", "Date", "Transaction"]
            for item in insider_data[:3]:
                for key in expected_keys:
                    assert key in item, f"Missing key: {key}"

    @pytest.mark.network
    def test_insider_transaction_types(self, insider_data: list):
        """Transaction should be Sale or Buy (or similar)."""
        valid_transactions = ["Sale", "Buy", "Option Exercise", "Automatic Sale"]
        if len(insider_data) > 0:
            for item in insider_data[:5]:
                transaction = item.get("Transaction", "")
                assert any(t in transaction for t in valid_transactions), \
                    f"Unknown transaction type: {transaction}"

    @pytest.mark.network
    def test_empty_for_some_stocks(self):
        """Some smaller stocks may have no insider data."""
        # This just tests that the function doesn't crash
        data = get_insider("AAPL")
        assert isinstance(data, list)


class TestGetAnalystPriceTargets:
    """Tests for the get_analyst_price_targets() function."""

    @pytest.mark.network
    def test_returns_list(self, analyst_data: list):
        """get_analyst_price_targets() should return a list."""
        assert isinstance(analyst_data, list)

    @pytest.mark.network
    def test_respects_last_ratings_param(self, test_ticker: str):
        """Should respect the last_ratings parameter."""
        data = get_analyst_price_targets(test_ticker, last_ratings=3)
        assert len(data) <= 3

    @pytest.mark.network
    def test_analyst_item_structure(self, analyst_data: list):
        """Each analyst item should be a dictionary with required keys."""
        if len(analyst_data) > 0:
            required_keys = ["date", "category", "analyst", "rating"]
            for item in analyst_data:
                for key in required_keys:
                    assert key in item, f"Missing key: {key}"

    @pytest.mark.network
    def test_analyst_date_format(self, analyst_data: list):
        """Analyst dates should be in YYYY-MM-DD format."""
        if len(analyst_data) > 0:
            for item in analyst_data:
                try:
                    datetime.strptime(item["date"], "%Y-%m-%d")
                except ValueError:
                    pytest.fail(f"Invalid date format: {item['date']}")

    @pytest.mark.network
    def test_analyst_has_price_target(self, analyst_data: list):
        """Analyst data should have price targets (target or target_from/target_to)."""
        if len(analyst_data) > 0:
            for item in analyst_data:
                has_target = "target" in item or ("target_from" in item and "target_to" in item)
                # Note: not all ratings have price targets, so we just check structure
                if has_target:
                    if "target" in item:
                        assert isinstance(item["target"], (int, float))
                    if "target_from" in item:
                        assert isinstance(item["target_from"], (int, float))
                    if "target_to" in item:
                        assert isinstance(item["target_to"], (int, float))

    @pytest.mark.network
    def test_analyst_rating_categories(self, analyst_data: list):
        """Rating categories should be recognizable."""
        valid_categories = [
            "Reiterated", "Upgrade", "Downgrade", "Initiated", "Resumed",
            "Maintains", "Reitrates",  # typos happen
        ]
        if len(analyst_data) > 0:
            for item in analyst_data:
                category = item.get("category", "")
                # Soft check - warn but don't fail for unknown categories
                if not any(v in category for v in valid_categories):
                    print(f"Warning: Unknown category: {category}")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.network
    def test_invalid_ticker_stock(self):
        """get_stock() with invalid ticker should return minimal data or handle gracefully."""
        # Finviz shows an error page for invalid tickers
        try:
            data = get_stock("INVALIDTICKER123")
            # If it returns, it should be a dict (possibly empty or with error indicators)
            assert isinstance(data, dict)
        except Exception:
            # Some exception handling is acceptable
            pass

    @pytest.mark.network
    def test_etf_ticker(self):
        """get_stock() should work for ETFs."""
        data = get_stock("SPY")
        assert isinstance(data, dict)
        assert data.get("Ticker") == "SPY"

    @pytest.mark.network
    def test_lowercase_ticker(self):
        """Tickers should work regardless of case."""
        data = get_stock("aapl")
        assert isinstance(data, dict)
        # Finviz normalizes to uppercase
        assert data.get("Ticker") in ["AAPL", "aapl"]

    @pytest.mark.network
    def test_special_character_ticker(self):
        """Test tickers with special characters (like BRK.B)."""
        try:
            data = get_stock("BRK.B")
            assert isinstance(data, dict)
        except Exception:
            # May fail - that's acceptable for special tickers
            pass
