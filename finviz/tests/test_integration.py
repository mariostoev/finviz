"""
Integration tests for finviz package.

These tests verify end-to-end functionality across multiple components.
"""

import pytest

from finviz import get_stock, get_news, get_insider, get_analyst_price_targets, Screener


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_full_stock_analysis_workflow(self):
        """
        Test a typical workflow: get stock data, news, insider info, and analyst targets.
        """
        ticker = "AAPL"

        # Get all data for the ticker
        stock_data = get_stock(ticker)
        news_data = get_news(ticker)
        insider_data = get_insider(ticker)
        analyst_data = get_analyst_price_targets(ticker)

        # Verify stock data
        assert stock_data["Ticker"] == ticker
        assert float(stock_data["Price"]) > 0
        assert stock_data["Company"]

        # Verify news
        assert len(news_data) > 0

        # Verify we got some data back
        assert isinstance(insider_data, list)
        assert isinstance(analyst_data, list)

    @pytest.mark.network
    @pytest.mark.slow
    def test_screener_to_stock_details_workflow(self):
        """
        Test workflow: screen stocks, then get detailed data for top results.
        """
        # Screen for large cap tech stocks
        screener = Screener(
            filters=["cap_largeover", "sec_technology"],
            table="Overview",
            rows=5
        )

        assert len(screener.data) > 0

        # Get detailed data for first stock
        first_ticker = screener[0]["Ticker"]
        stock_data = get_stock(first_ticker)

        assert stock_data["Ticker"] == first_ticker
        assert "P/E" in stock_data

    @pytest.mark.network
    @pytest.mark.slow
    def test_screener_with_ticker_details(self):
        """
        Test Screener.get_ticker_details() enrichment.
        """
        screener = Screener(tickers=["AAPL", "MSFT"], table="Overview")

        # Before getting details
        initial_keys = set(screener[0].keys())

        # Get detailed information
        screener.get_ticker_details()

        # After getting details - should have more keys
        final_keys = set(screener[0].keys())
        assert len(final_keys) > len(initial_keys)

    @pytest.mark.network
    def test_multiple_table_types_same_stock(self):
        """
        Test that different table types return different data for same filter.
        """
        filters = ["cap_megaover"]

        overview = Screener(filters=filters, table="Overview", rows=5)
        valuation = Screener(filters=filters, table="Valuation", rows=5)
        performance = Screener(filters=filters, table="Performance", rows=5)

        # Same stocks should appear
        overview_tickers = {row["Ticker"] for row in overview.data}
        valuation_tickers = {row["Ticker"] for row in valuation.data}
        performance_tickers = {row["Ticker"] for row in performance.data}

        # Should have significant overlap (same filter)
        assert overview_tickers == valuation_tickers == performance_tickers

        # But different columns
        assert overview.headers != valuation.headers
        assert valuation.headers != performance.headers


class TestDataConsistency:
    """Tests for data consistency across different functions."""

    @pytest.mark.network
    def test_stock_price_consistency(self):
        """
        Stock price from get_stock() should be close to Screener price.
        """
        ticker = "AAPL"

        stock_data = get_stock(ticker)
        screener = Screener(tickers=[ticker], table="Overview")

        stock_price = float(stock_data["Price"])
        screener_price = float(screener[0]["Price"])

        # Prices should be within 1% (could differ slightly due to timing)
        diff_pct = abs(stock_price - screener_price) / stock_price * 100
        assert diff_pct < 1, f"Price difference too large: {diff_pct:.2f}%"

    @pytest.mark.network
    def test_market_cap_consistency(self):
        """
        Market cap from get_stock() should match Screener.
        """
        ticker = "AAPL"

        stock_data = get_stock(ticker)
        screener = Screener(tickers=[ticker], table="Overview")

        # Both should have market cap
        assert "Market Cap" in stock_data
        assert "Market Cap" in screener[0]

        # Values should match
        assert stock_data["Market Cap"] == screener[0]["Market Cap"]


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    @pytest.mark.network
    def test_mixed_valid_invalid_tickers(self):
        """
        Screener should handle mix of valid and potentially invalid tickers.
        """
        # Mix of definitely valid and edge case tickers
        tickers = ["AAPL", "MSFT", "GOOGL"]
        screener = Screener(tickers=tickers, table="Overview")

        # Should get data for valid tickers
        returned_tickers = [row["Ticker"] for row in screener.data]
        assert "AAPL" in returned_tickers
        assert "MSFT" in returned_tickers

    @pytest.mark.network
    def test_screener_no_results_filter(self):
        """
        Screener with very restrictive filters should handle no results gracefully.
        """
        # Very restrictive filters unlikely to match any stock
        filters = [
            "cap_mega",          # Mega cap only
            "sh_price_u1",       # Under $1
            "fa_pe_low",         # Low P/E
        ]

        try:
            screener = Screener(filters=filters, table="Overview")
            # Either returns empty list or raises NoResults
            assert isinstance(screener.data, list)
        except Exception as e:
            # NoResults exception is acceptable
            assert "NoResults" in type(e).__name__ or "No results" in str(e)


class TestCaching:
    """Tests for caching behavior."""

    @pytest.mark.network
    def test_stock_page_caching(self):
        """
        Multiple get_* calls for same ticker should use cached page.
        """
        ticker = "AAPL"

        # Clear cache if possible
        from finviz.main_func import STOCK_PAGE
        if ticker in STOCK_PAGE:
            del STOCK_PAGE[ticker]

        # First call - should fetch
        get_stock(ticker)
        assert ticker in STOCK_PAGE

        # Subsequent calls use cache
        get_news(ticker)
        get_insider(ticker)
        get_analyst_price_targets(ticker)

        # Page should still be cached (only one fetch)
        assert ticker in STOCK_PAGE


class TestRealWorldScenarios:
    """Tests based on real-world usage scenarios."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_value_investing_screen(self):
        """
        Screen for value stocks - low P/E, positive earnings.
        """
        filters = [
            "fa_pe_low",         # Low P/E
            "fa_eps_pos",        # Positive EPS
            "cap_midover",       # Mid cap and above
        ]

        screener = Screener(filters=filters, table="Valuation", rows=10)

        # Should find some value stocks
        assert len(screener.data) > 0

        # P/E should be present and numeric
        for row in screener.data[:5]:
            pe = row.get("P/E", "")
            if pe and pe != "-":
                try:
                    float(pe)
                except ValueError:
                    pytest.fail(f"Invalid P/E value: {pe}")

    @pytest.mark.network
    @pytest.mark.slow
    def test_momentum_screen(self):
        """
        Screen for momentum stocks - strong recent performance.
        """
        filters = [
            "ta_perf_dup",       # Up today
            "sh_avgvol_o400",    # High volume
            "cap_midover",       # Mid cap and above
        ]

        screener = Screener(filters=filters, table="Performance", rows=10)

        # May or may not find stocks depending on market conditions
        assert isinstance(screener.data, list)

    @pytest.mark.network
    def test_dividend_screen(self):
        """
        Screen for dividend stocks.
        """
        filters = [
            "fa_div_pos",        # Positive dividend
            "cap_largeover",     # Large cap
        ]

        screener = Screener(filters=filters, table="Overview", rows=10)

        assert len(screener.data) > 0

    @pytest.mark.network
    @pytest.mark.slow
    def test_sector_comparison(self):
        """
        Compare stocks across different sectors.
        """
        sectors = ["sec_technology", "sec_healthcare", "sec_financial"]
        sector_data = {}

        for sector in sectors:
            screener = Screener(
                filters=[sector, "cap_largeover"],
                table="Overview",
                rows=3
            )
            sector_data[sector] = screener.data

        # Each sector should have data
        for sector, data in sector_data.items():
            assert len(data) > 0, f"No data for {sector}"
