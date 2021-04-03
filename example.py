#!/usr/bin/python3

from finviz.screener import Screener

# Get dict of available filters
# filters dict contains the corresponding filter tags
filters = Screener.load_filter_dict()
some_filters = [filters["PEG"]["Under 1"], filters["Exchange"]["AMEX"]]
stock_list = Screener(filters=some_filters, order="ticker")
print(stock_list)

# Use raw filter tags in a list
# filters = ['geo_usa']
filters = ["idx_sp500"]  # Shows companies in the S&P500
print("Screening stocks...")
stock_list = Screener(filters=filters, order="ticker")
print(stock_list)

print("Retrieving stock data...")
stock_data = stock_list.get_ticker_details()
print(stock_data)

# Export the screener results to CSV file
stock_list.to_csv("sp500.csv")

# Create a SQLite database
# stock_list.to_sqlite("sp500.sqlite")
