from finviz.screener import Screener


class TestScreener:
	""" Unit tests for Screener app """
	def test_get_screener_data_sequential_requests(self):
		stocks = Screener(filters=['sh_curvol_o300', 'ta_highlow52w_b0to10h', 'ind_stocksonly'])

		count = 0
		for _ in stocks:
			count += 1

		assert len(stocks) == count

	def test_get_ticker_details_sequential_requests(self):
		stocks = Screener(filters=['sh_curvol_o300', 'ta_highlow52w_b0to10h', 'ind_stocksonly', 'sh_outstanding_o1000'])
		ticker_details = stocks.get_ticker_details()

		count = 0
		for _ in ticker_details:
			count += 1

		assert len(stocks) == count == len(ticker_details)
