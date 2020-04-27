#!/usr/bin/python3

from finviz.helper_functions.save_data import export_to_db, export_to_csv
from finviz.screener import Screener
from finviz.main_func import *

#filters = []
#filters = ['geo_usa']
filters = ['idx_sp500']  # Shows companies in the S&P500
print("Filtering stocks..")
stock_list = Screener(filters=filters, order='ticker')
print("Parsing every stock..")
stock_list.get_ticker_details()

# Export the screener results to CSV file
stock_list.to_csv('sp500.csv')

# Create a SQLite database
#stock_list.to_sqlite('sp500.sqlite')
