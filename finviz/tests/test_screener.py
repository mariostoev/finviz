from unittest.mock import patch

import lxml
from dateutil.parser import parse

from finviz.main_func import get_all_news, get_analyst_price_targets
from finviz.screener import Screener


class TestScreener:
    """ Unit tests for Screener app """

    def test_get_screener_data_sequential_requests(self):
        """ Tests that basic Screener example returns correct number of stocks. """
        stock_list = Screener(
            filters=["sh_curvol_o300", "ta_highlow52w_b0to10h", "ind_stocksonly"]
        )

        count = 0
        for _ in stock_list:
            count += 1

        assert len(stock_list) == count

    def test_screener_stability(self):
        """ Requested in #77: https://github.com/mariostoev/finviz/issues/77 """
        filters = [
            "sh_avgvol_o100",  # average daily volume > 100k shares
            "sh_curvol_o100",  # current daily volume > 100k shares
            "sh_float_u50",  # floating stocks < 50m shares
            "sh_price_u3",  # current price is under $3
        ]
        stock_list = Screener(filters=filters, table="Performance")

        count = 0
        for _ in stock_list:
            count += 1

        assert len(stock_list) == count

    def test_get_ticker_details_sequential_requests(self):
        """ Tests that `get_ticker_details` method returns correct number of ticker details. """
        stocks = Screener(
            filters=[
                "sh_curvol_o300",
                "ta_highlow52w_b0to10h",
                "ind_stocksonly",
                "sh_outstanding_o1000",
            ]
        )
        ticker_details = stocks.get_ticker_details()

        count = 0
        for _ in ticker_details:
            count += 1

        assert len(stocks) == count == len(ticker_details)

    @patch("finviz.screener.scrape.download_chart_image")
    def test_get_charts_sequential_requests(self, patched_download_chart_image):
        """ Tests that `get_charts` method returns correct number of valid charts. """

        stocks = Screener(
            filters=[
                "sh_curvol_o20000",
                "ta_highlow52w_b0to10h",
                "ind_stocksonly",
                "sh_outstanding_o1000",
            ]
        )

        count = 0
        for _ in stocks:
            count += 1

        stocks.get_charts()

        for call in patched_download_chart_image.call_args_list:
            assert call.kwargs["URL"]
            assert call.args[0]
        assert len(stocks) == count == patched_download_chart_image.call_count


def test_get_analyst_price_targets():
    """ Verifies `get_analyst_price_targets` results' types are valid. """

    price_target = get_analyst_price_targets("AAPL")[0]
    assert price_target

    try:
        parse(price_target["date"])
    except ValueError:
        assert False

    assert type(price_target["category"]) == lxml.etree._ElementUnicodeResult
    assert type(price_target["analyst"]) == lxml.etree._ElementUnicodeResult
    assert type(price_target["rating"]) == lxml.etree._ElementUnicodeResult
    assert type(price_target.get("price_from", 0.0)) == float
    assert type(price_target.get("price_to", 0.0)) == float


def test_get_all_news():
    """ Verifies news results are greater than 0. """
    news = get_all_news()
    assert len(news) > 0
