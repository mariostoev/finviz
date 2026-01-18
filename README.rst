finviz-api
##########
*Unofficial Python API for FinViz*

.. image:: https://badge.fury.io/py/finviz.svg
    :target: https://badge.fury.io/py/finviz

.. image:: https://img.shields.io/badge/python-3.10+-blue.svg
    :target: https://www.python.org/downloads/

.. image:: https://pepy.tech/badge/finviz
    :target: https://pepy.tech/project/finviz

.. image:: https://github.com/mariostoev/finviz/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mariostoev/finviz/actions


What's New in v2.0
==================

**v2.0.0** is a major update that fixes all scraping issues caused by FinViz website changes:

- Fixed ``get_stock()`` - now returns 90+ data points
- Fixed ``Screener`` - table parsing and header extraction
- Fixed ``get_news()`` - handles new timestamp formats
- Fixed ``get_insider()`` - supports new table structure
- Fixed ``get_analyst_price_targets()`` - updated selectors
- **Python 3.10+** required (dropped 3.9 support)
- Comprehensive test suite with real API testing

See `CHANGELOG.md <CHANGELOG.md>`_ for full details.


Installation
============

.. code:: bash

    pip install finviz

Or install the latest development version:

.. code:: bash

    pip install git+https://github.com/mariostoev/finviz@v2-development


What is Finviz?
===============

FinViz_ aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools, and charts.

.. _FinViz: https://finviz.com

**Important Information**

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpose is financial analysis, research, and data scraping.


Quick Start
===========

.. code:: python

    import finviz

    # Get stock data
    stock = finviz.get_stock('AAPL')
    print(stock['Price'], stock['P/E'], stock['Market Cap'])

    # Get news
    news = finviz.get_news('AAPL')
    for timestamp, headline, url, source in news[:5]:
        print(f"{timestamp} - {headline} ({source})")

    # Get insider transactions
    insiders = finviz.get_insider('AAPL')
    for trade in insiders[:3]:
        print(trade['Insider Trading'], trade['Transaction'], trade['Value ($)'])

    # Get analyst price targets
    targets = finviz.get_analyst_price_targets('AAPL')
    for target in targets:
        print(target['analyst'], target['rating'], target.get('target_to'))


Using Screener
==============

The Screener allows you to filter stocks based on various criteria. You can either build filters programmatically or copy them from the FinViz website URL.

.. code:: python

    from finviz.screener import Screener

    # Screen for large-cap NASDAQ stocks in the S&P 500
    filters = ['exch_nasd', 'idx_sp500', 'cap_largeover']
    stock_list = Screener(filters=filters, table='Overview', order='price')

    print(f"Found {len(stock_list)} stocks")

    for stock in stock_list[:10]:
        print(stock['Ticker'], stock['Company'], stock['Market Cap'])

    # Export to CSV
    stock_list.to_csv("stocks.csv")

    # Export to SQLite
    stock_list.to_sqlite("stocks.sqlite3")

**Available Tables:**

- ``Overview`` - Basic company info, market cap, price
- ``Valuation`` - P/E, P/S, P/B, PEG ratios
- ``Financial`` - ROA, ROE, ROI, margins
- ``Ownership`` - Insider/institutional ownership, short interest
- ``Performance`` - Price performance across timeframes
- ``Technical`` - RSI, SMA, volatility, beta

**Initialize from URL:**

.. code:: python

    # Copy filters directly from FinViz website URL
    url = "https://finviz.com/screener.ashx?v=111&f=cap_largeover,exch_nasd&o=-marketcap"
    stock_list = Screener.init_from_url(url)

**Get Available Filters:**

.. code:: python

    # Get all available filter options
    filters = Screener.load_filter_dict()
    print(filters.keys())  # ['Exchange', 'Index', 'Sector', 'Industry', ...]


Individual Stock Functions
==========================

.. code:: python

    import finviz

    # Comprehensive stock data (90+ metrics)
    stock = finviz.get_stock('AAPL')
    # Returns: {'Ticker': 'AAPL', 'Company': 'Apple Inc', 'Sector': 'Technology',
    #           'P/E': '34.26', 'Market Cap': '3755.76B', 'Price': '255.53', ...}

    # Recent news with timestamps
    news = finviz.get_news('AAPL')
    # Returns: [('2024-01-15 12:00', 'Headline...', 'https://...', 'MarketWatch'), ...]

    # Insider trading activity
    insiders = finviz.get_insider('AAPL')
    # Returns: [{'Insider Trading': 'COOK TIMOTHY D', 'Relationship': 'CEO',
    #            'Transaction': 'Sale', 'Value ($)': '41,530,891', ...}, ...]

    # Analyst ratings and price targets
    targets = finviz.get_analyst_price_targets('AAPL', last_ratings=10)
    # Returns: [{'date': '2024-01-09', 'analyst': 'Morgan Stanley',
    #            'rating': 'Overweight', 'target_from': 200, 'target_to': 220}, ...]

    # All market news (not ticker-specific)
    all_news = finviz.get_all_news()


Using Portfolio
===============

.. code:: python

    from finviz.portfolio import Portfolio

    portfolio = Portfolio('<email>', '<password>', '<portfolio-name>')
    print(portfolio)

    # Create portfolio from CSV
    portfolio.create_portfolio('My Portfolio', 'positions.csv')

CSV format for portfolio import:

.. list-table::
   :header-rows: 1

   * - Ticker
     - Transaction
     - Date (Opt.)
     - Shares
     - Price (Opt.)
   * - AAPL
     - 1
     - 05-25-2024
     - 34
     - 185.50
   * - NVDA
     - 1
     -
     - 100
     -

*Transaction: 1 = Buy, 2 = Sell. Empty optional fields use today's data.*


Downloading Charts
==================

.. code:: python

    stock_list.get_charts(period='d', chart_type='c', size='l', ta='1')

    # period: 'd' (daily), 'w' (weekly), 'm' (monthly)
    # chart_type: 'c' (candle), 'l' (line)
    # size: 's' (small), 'l' (large)
    # ta: '1' (show technical analysis), '0' (hide)


Configuration
=============

**Environment Variables:**

- ``DISABLE_TQDM=1`` - Disable progress bars

**Async Support:**

The Screener supports async requests for faster data fetching:

.. code:: python

    stock_list = Screener(filters=filters, request_method="async")


Development
===========

.. code:: bash

    # Clone and install in development mode
    git clone https://github.com/mariostoev/finviz
    cd finviz
    pip install -e ".[dev]"

    # Run tests
    pytest finviz/tests/ -v

    # Run tests (skip slow ones)
    pytest finviz/tests/ -v -m "not slow"


*You can also buy me a coffee!*

.. image:: https://user-images.githubusercontent.com/8982949/33011169-6da4af5e-cddd-11e7-94e5-a52d776b94ba.png
        :target: https://www.paypal.me/finvizapi


Disclaimer
==========

*Using this library to acquire data from FinViz may be against their Terms of Service. Use it responsibly and at your own risk. This library is built for educational purposes.*

