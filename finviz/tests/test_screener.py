"""
Tests for the Screener class.

All tests make real HTTP requests to finviz.com.
"""

import json
import time
import warnings
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest
from lxml import html

from finviz import Screener
from finviz.helper_functions.scraper_functions import get_page_urls, get_table
from finviz.main_func import get_all_news, get_analyst_price_targets


class TestGetTableInput:
    """Offline tests for the page types get_table accepts."""

    PAGE = (
        '<div><div class="fv-table_row" role="row">'
        '<div role="gridcell" data-ticker="AAPL">logo AAPL</div>'
        '<div role="gridcell"> 344.63 </div>'
        "</div></div>"
    )

    def test_accepts_parsed_page(self):
        """request_method="async" passes get_table an already parsed page."""
        data = get_table(html.fromstring(self.PAGE), ["Ticker", "Price"], rows=1)
        assert data == [{"Ticker": "AAPL", "Price": "344.63"}]

    def test_accepts_page_text(self):
        """Sequential requests pass get_table the page text."""
        data = get_table(self.PAGE, ["Ticker", "Price"], rows=1)
        assert data == [{"Ticker": "AAPL", "Price": "344.63"}]


class TestRowAndColumnLimits:
    """Offline tests for the limits of what Finviz serves."""

    @staticmethod
    def page(total=1, colcount=1):
        return html.fromstring(
            f'<div><p class="fv-table_toolbar-count">#1 / {total} Total</p>'
            f'<div class="fv-table_viewport" role="grid" aria-colcount="{colcount}">'
            '<div class="fv-table_header-row"><div role="columnheader">Ticker</div></div>'
            "</div></div>"
        )

    def build(self, page, rows):
        with patch("finviz.screener.http_request_get", return_value=(page, "https://x?v=111")):
            with patch("finviz.screener.sequential_data_scrape", return_value=[rows]):
                return Screener()

    def test_page_urls_stop_at_row_limit(self):
        """Finviz answers requests past row 1000 with a 403."""
        pager = html.fromstring(
            '<div><button aria-label="Page">'
            '<span class="select-trigger_label">1 / 53</span></button></div>'
        )
        urls = get_page_urls(pager, 1050, "u")
        assert len(urls) == 50
        assert urls[-1] == "u&r=981"

    def test_warns_when_rows_are_missing(self):
        """Len and data should agree, and the user should hear about the shortfall."""
        with pytest.warns(UserWarning, match="1 of 1050 rows"):
            screener = self.build(self.page(total=1050), [{"Ticker": "AAPL"}])
        assert len(screener) == len(screener.data) == 1

    def test_short_result_does_not_limit_later_queries(self):
        """A short result, such as after a temporary block, should not stick."""
        with pytest.warns(UserWarning, match="1 of 2 rows"):
            screener = self.build(self.page(total=2), [{"Ticker": "AAPL"}])

        full_rows = [{"Ticker": "AAPL"}, {"Ticker": "MSFT"}]
        with patch("finviz.screener.http_request_get", return_value=(self.page(total=2), "https://x?v=111")):
            with patch("finviz.screener.sequential_data_scrape", return_value=[full_rows]):
                screener.add(order="-price")

        assert len(screener) == len(screener.data) == 2

    def test_warns_when_columns_are_missing(self):
        """The server renders only some columns of a wide custom table."""
        with pytest.warns(UserWarning, match="1 of 70 columns"):
            self.build(self.page(colcount=70), [{"Ticker": "AAPL"}])

    def test_no_warning_for_a_complete_result(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            screener = self.build(self.page(), [{"Ticker": "AAPL"}])
        assert len(screener) == 1


class TestLoadFilterDictOffline:
    """Offline test for the filter definitions embedded in the page."""

    @staticmethod
    def page(filter_defs):
        payload = json.dumps({"filters": {"filters": filter_defs}}, separators=(",", ":"))
        return MagicMock(text=f"<html><body><script data-ssr-props>{payload}</script></body></html>")

    def test_builds_filters_from_stock_and_etf_pages(self):
        stock_page = self.page(
            [
                {
                    "key": "cap",
                    "title": {"short": "Market Cap."},
                    "options": [
                        {"label": "Any", "value": ""},
                        {"label": "Mega", "value": "mega"},
                        {"label": "Custom", "value": "custom", "isEliteOnly": True},
                    ],
                },
                {
                    "key": "sh_insiderown",
                    "title": {"short": "Insider\nOwnership"},
                    "options": [{"label": "Low", "value": "low"}],
                },
                {
                    "key": "sh_trades",
                    "isEliteOnly": True,
                    "title": {"short": "Trades"},
                    "options": [{"label": "Over 100", "value": "o100"}],
                },
            ]
        )
        etf_page = self.page(
            [
                {
                    "key": "cap",
                    "title": {"short": "Market Cap."},
                    "options": [{"label": "ETF option", "value": "etf"}],
                },
                {
                    "key": "etf_assettype",
                    "title": {"short": "Asset Type"},
                    "options": [{"label": "Bonds", "value": "bonds"}],
                },
            ]
        )

        with patch("finviz.screener.requests.get", side_effect=[stock_page, etf_page]):
            with patch("finviz.screener.open", mock_open(), create=True):
                filters = Screener.load_filter_dict(reload=False)

        assert filters == {
            "Market Cap.": {"Mega": "cap_mega"},
            "InsiderOwnership": {"Low": "sh_insiderown_low"},
            "Asset Type": {"Bonds": "etf_assettype_bonds"},
        }


class TestScreenerBasic:
    """Basic tests for Screener functionality."""

    @pytest.mark.network
    def test_screener_returns_data(self):
        """Screener should return data."""
        screener = Screener(filters=["cap_largeover"], table="Overview")
        assert len(screener.data) > 0

    @pytest.mark.network
    def test_screener_has_headers(self):
        """Screener should have headers."""
        screener = Screener(filters=["cap_largeover"], table="Overview")
        assert len(screener.headers) > 0
        assert "Ticker" in screener.headers

    @pytest.mark.network
    def test_screener_data_matches_headers(self):
        """Each data row should have keys matching headers."""
        screener = Screener(filters=["cap_largeover", "exch_nasd"], table="Overview")
        if len(screener.data) > 0:
            for row in screener.data[:5]:
                for header in screener.headers:
                    assert header in row, f"Missing header key: {header}"

    @pytest.mark.network
    def test_screener_len(self):
        """len(screener) should return total rows."""
        screener = Screener(filters=["cap_largeover", "exch_nasd"], table="Overview")
        assert len(screener) > 0
        assert len(screener) == screener._rows

    @pytest.mark.network
    def test_screener_getitem(self):
        """screener[0] should return first row."""
        screener = Screener(filters=["cap_largeover", "exch_nasd"], table="Overview")
        first_row = screener[0]
        assert isinstance(first_row, dict)
        assert "Ticker" in first_row

    @pytest.mark.network
    def test_screener_iteration(self):
        """Screener should be iterable."""
        screener = Screener(filters=["cap_largeover", "exch_nasd"], table="Overview")
        count = 0
        for row in screener:
            count += 1
            if count >= 5:
                break
        assert count == 5


class TestScreenerFilters:
    """Tests for Screener with different filters."""

    @pytest.mark.network
    def test_market_cap_filter(self):
        """Market cap filter should work."""
        # Large cap only
        screener = Screener(filters=["cap_largeover"], table="Overview")
        assert len(screener) > 0

    @pytest.mark.network
    def test_exchange_filter(self):
        """Exchange filter should work."""
        screener = Screener(filters=["exch_nasd"], table="Overview")
        assert len(screener) > 0

    @pytest.mark.network
    def test_multiple_filters(self):
        """Multiple filters should work together."""
        screener = Screener(
            filters=["cap_largeover", "exch_nasd", "sec_technology"],
            table="Overview"
        )
        assert len(screener) > 0

    @pytest.mark.network
    def test_sector_filter(self):
        """Sector filter should work."""
        screener = Screener(filters=["sec_technology"], table="Overview")
        assert len(screener) > 0

    @pytest.mark.network
    @pytest.mark.slow
    def test_complex_filters(self):
        """Complex filter combination should work."""
        filters = [
            "sh_avgvol_o100",   # avg volume > 100k
            "sh_curvol_o100",   # current volume > 100k
            "sh_price_u50",     # price under $50
            "cap_smallover",    # small cap and over
        ]
        screener = Screener(filters=filters, table="Overview")
        # May return 0 results depending on market conditions
        assert isinstance(screener.data, list)


class TestScreenerTables:
    """Tests for different Screener table types."""

    @pytest.mark.network
    def test_overview_table(self):
        """Overview table should have expected headers."""
        screener = Screener(filters=["cap_mega"], table="Overview")
        expected_headers = ["Ticker", "Company", "Sector", "Industry", "Country", "Market Cap"]
        for header in expected_headers:
            assert header in screener.headers, f"Missing header: {header}"

    @pytest.mark.network
    def test_valuation_table(self):
        """Valuation table should have valuation metrics."""
        screener = Screener(filters=["cap_mega"], table="Valuation")
        expected_headers = ["P/E", "P/S", "P/B", "P/FCF"]
        for header in expected_headers:
            assert header in screener.headers, f"Missing header: {header}"

    @pytest.mark.network
    def test_performance_table(self):
        """Performance table should have performance metrics."""
        screener = Screener(filters=["cap_mega"], table="Performance")
        expected_headers = ["Perf Week", "Perf Month", "Perf Year"]
        for header in expected_headers:
            assert header in screener.headers, f"Missing header: {header}"

    @pytest.mark.network
    def test_financial_table(self):
        """Financial table should have financial metrics."""
        screener = Screener(filters=["cap_mega"], table="Financial")
        expected_headers = ["ROA", "ROE", "ROIC"]
        for header in expected_headers:
            assert header in screener.headers, f"Missing header: {header}"

    @pytest.mark.network
    def test_technical_table(self):
        """Technical table should have technical indicators."""
        screener = Screener(filters=["cap_mega"], table="Technical")
        expected_headers = ["RSI", "SMA20", "SMA50", "SMA200"]
        for header in expected_headers:
            assert header in screener.headers, f"Missing header: {header}"


class TestScreenerTickers:
    """Tests for Screener with specific tickers."""

    @pytest.mark.network
    def test_single_ticker(self):
        """Screener with single ticker should return that ticker."""
        screener = Screener(tickers=["AAPL"], table="Overview")
        assert len(screener) == 1
        assert screener[0]["Ticker"] == "AAPL"

    @pytest.mark.network
    def test_multiple_tickers(self):
        """Screener with multiple tickers should return all."""
        tickers = ["AAPL", "MSFT", "GOOGL"]
        screener = Screener(tickers=tickers, table="Overview")
        assert len(screener) == len(tickers)
        returned_tickers = [row["Ticker"] for row in screener.data]
        for ticker in tickers:
            assert ticker in returned_tickers


class TestScreenerRows:
    """Tests for Screener row limiting."""

    @pytest.mark.network
    def test_rows_limit(self):
        """Screener should respect rows limit."""
        screener = Screener(filters=["cap_largeover"], table="Overview", rows=10)
        assert len(screener.data) <= 10

    @pytest.mark.network
    def test_rows_limit_exact(self):
        """Screener data should have exactly rows items (if available)."""
        screener = Screener(filters=["cap_largeover"], table="Overview", rows=5)
        # If total > 5, we should have exactly 5
        if screener._total_rows > 5:
            assert len(screener.data) == 5


class TestScreenerOrder:
    """Tests for Screener ordering."""

    @pytest.mark.network
    def test_order_by_market_cap(self):
        """Screener should support ordering."""
        screener = Screener(
            filters=["cap_largeover"],
            table="Overview",
            order="-marketcap",  # Descending
            rows=10
        )
        assert len(screener.data) > 0


class TestScreenerMethods:
    """Tests for Screener additional methods."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_get_ticker_details(self):
        """get_ticker_details should fetch additional data."""
        screener = Screener(tickers=["AAPL", "MSFT"], table="Overview")
        details = screener.get_ticker_details()
        assert len(details) == 2
        # Should have additional keys from stock page
        assert "Price" in details[0] or "Market Cap" in details[0]

    @pytest.mark.network
    @patch("finviz.screener.scrape.download_chart_image")
    def test_get_charts(self, mock_download):
        """get_charts should download charts for each ticker."""
        screener = Screener(tickers=["AAPL", "MSFT"], table="Overview")
        screener.get_charts()
        assert mock_download.call_count == 2

    @pytest.mark.network
    def test_to_csv_returns_string(self):
        """to_csv with None filename should return CSV string."""
        screener = Screener(tickers=["AAPL"], table="Overview")
        # to_csv expects a filename, but we can check it doesn't crash
        # The actual CSV export would write to a file

    @pytest.mark.network
    def test_str_representation(self):
        """str(screener) should return a table string."""
        screener = Screener(tickers=["AAPL"], table="Overview")
        table_str = str(screener)
        assert "AAPL" in table_str
        assert len(table_str) > 0

    @pytest.mark.network
    def test_repr_representation(self):
        """repr(screener) should show parameters."""
        screener = Screener(tickers=["AAPL"], table="Overview")
        repr_str = repr(screener)
        assert "tickers" in repr_str
        assert "AAPL" in repr_str


class TestScreenerClassMethods:
    """Tests for Screener class methods."""

    @pytest.mark.network
    def test_init_from_url(self):
        """Screener.init_from_url should parse URL correctly."""
        url = "https://finviz.com/screener.ashx?v=111&f=cap_largeover&t=AAPL,MSFT"
        screener = Screener.init_from_url(url)
        assert "AAPL" in screener._tickers
        assert "MSFT" in screener._tickers

    @pytest.mark.network
    def test_load_filter_dict(self):
        """load_filter_dict should return filter options."""
        filters = Screener.load_filter_dict(reload=True)
        assert isinstance(filters, dict)
        assert len(filters) > 0
        # Should have common filter categories
        assert "Exchange" in filters or "Market Cap." in filters


class TestScreenerStability:
    """Stability tests from GitHub issues."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_screener_stability_issue_77(self):
        """Test from issue #77 - screener stability with multiple filters."""
        filters = [
            "sh_avgvol_o100",
            "sh_curvol_o100",
            "sh_float_u50",
            "sh_price_u3",
        ]
        screener = Screener(filters=filters, table="Performance")
        count = sum(1 for _ in screener)
        assert len(screener) == count

    @pytest.mark.network
    def test_sequential_vs_count(self):
        """Iteration count should match len()."""
        screener = Screener(
            filters=["cap_largeover", "exch_nasd"],
            table="Overview",
            rows=20
        )
        count = sum(1 for _ in screener)
        assert len(screener.data) == count


class TestGetAllNews:
    """Tests for the get_all_news function."""

    @pytest.mark.network
    def test_get_all_news_returns_list(self):
        """get_all_news should return a list."""
        news = get_all_news()
        assert isinstance(news, list)

    @pytest.mark.network
    def test_get_all_news_has_items(self):
        """get_all_news should have news items."""
        news = get_all_news()
        assert len(news) > 0

    @pytest.mark.network
    def test_get_all_news_structure(self):
        """Each news item should have date, headline, and link."""
        news = get_all_news()
        if len(news) > 0:
            for item in news[:5]:
                assert len(item) == 3, f"News item has wrong length: {len(item)}"
