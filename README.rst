finviz-api
##########
*Unofficial Python API for FinViz*

.. image:: https://badge.fury.io/py/finviz.svg
    :target: https://badge.fury.io/py/finviz
    
.. image:: https://img.shields.io/badge/python-3.9-blue.svg
    :target: https://www.python.org/downloads/release/python-390/
    
.. image:: https://pepy.tech/badge/finviz
    :target: https://pepy.tech/project/finviz
    

Downloading & Installation
---------------------------

    $ pip install -U git+https://github.com/mariostoev/finviz


What is Finviz?
================
FinViz_ aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools, and charts.

.. _FinViz: https://finviz.com/?a=128493348

**Important Information**

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpose is financial analysis, research, and data scraping.

Using Screener
===============

Before using the Screener class, you have to manually go to the website's screener and enter your desired settings. The URL will automatically change every time you add a new setting. After you're done the URL will look something like this:

.. image:: https://i.imgur.com/p8BLt06.png

``?v=111&s=ta_newhigh&f=cap_largeover,exch_nasd,fa_fpe_o10&o=-ticker&t=ZM`` are the extra parameters provided to the screener. Those parameters are a list of key/value pairs separated with the & symbol. Some keys have a clear intent - ``f=cap_largeover,exch_nasd,fa_fpe_o10`` are filters, ``o=-ticker`` is order and ``t=ZM`` are tickers - yet, some are ambiguous like ``v=111``, which stands for the type of table. 

To make matters easier inside the code you won't refer to tables by their number tag, but instead you will use their full name (ex. ``table=Performance``).

.. code:: python

    from finviz.screener import Screener

    filters = ['exch_nasd', 'idx_sp500']  # Shows companies in NASDAQ which are in the S&P500
    stock_list = Screener(filters=filters, table='Performance', order='price')  # Get the performance table and sort it by price ascending

    # Export the screener results to .csv 
    stock_list.to_csv("stock.csv")

    # Create a SQLite database 
    stock_list.to_sqlite("stock.sqlite3")

    for stock in stock_list[9:19]:  # Loop through 10th - 20th stocks 
        print(stock['Ticker'], stock['Price']) # Print symbol and price

    # Add more filters
    stock_list.add(filters=['fa_div_high'])  # Show stocks with high dividend yield
    # or just stock_list(filters=['fa_div_high'])

    # Print the table into the console
    print(stock_list)
    
.. image:: https://i.imgur.com/cb7UdxB.png

Using Portfolio
================
.. code:: python

    from finviz.portfolio import Portfolio

    portfolio = Portfolio('<your-email-address>', '<your-password>', '<portfolio-name>')
    # Print the portfolio into the console
    print(portfolio)
    
*Note that, portfolio name is optional - it would assume your default portfolio (if you have one) if you exclude it.*
The Portfolio class can also create new portfolio from an existing ``.csv`` file. The ``.csv`` file must be in the following format:


.. list-table:: 
   :header-rows: 1

   * - Ticker
     - Transaction  
     - Date (Opt.)
     - Shares
     - Price (Opt.)
   * - AAPL
     - 1
     - 05-25-2017
     - 34
     - 141.28
   * - NVDA
     - 2
     - 
     - 250
     - 243.32
   * - WMT
     - 1
     - 01.19.2019
     - 45
     - 
 
Note that, if any *optional* fields are left empty, the API will assign them today's data.

.. code:: python

    portfolio.create_portfolio('<portfolio-name>', '<path-to-csv-file>')

Individual stocks
==================

.. code:: pycon

    >>> import finviz
    >>> finviz.get_stock('AAPL')
    {'Index': 'DJIA S&P500', 'P/E': '12.91', 'EPS (ttm)': '12.15',...
    >>> finviz.get_insider('АAPL')
    [{'Insider Trading': 'KONDO CHRIS', 'Relationship': 'Principal Accounting Officer', 'Date': 'Nov 19', 'Transaction':            'Sale', 'Cost': '190.00', '#Shares': '3,408', 'Value ($)': '647,520', '#Shares Total': '8,940', 'SEC Form 4': 'Nov 21           06:31 PM'},...
    >>> finviz.get_news('AAPL')
    [('Chinas Economy Slows to the Weakest Pace Since 2009', 'https://finance.yahoo.com/news/china-economy-slows-weakest-pace-      020040147.html'),...
    >>>
    >>> finviz.get_analyst_price_targets('AAPL')
    [{'date': '2019-10-24', 'category': 'Reiterated', 'analyst': 'UBS', 'rating': 'Buy', 'price_from': 235, 'price_to': 275}, ...

Downloading charts
===================

.. code:: python
    
    # Monthly, Candles, Large, No Technical Analysis
    stock_list.get_charts(period='m', chart_type='c', size='l', ta='0')
    
    # period='d' > daily 
    # period='w' > weekly
    # period='m' > monthly
    
    # chart_type='c' > candle
    # chart_type='l' > lines
    
    # size='m' > small
    # size='l' > large
    
    # ta='1' > display technical analysis
    # ta='0' > ignore technical analysis
    
Environment Variables
======================

Set ``DISABLE_TQDM=1`` in your environment to disable the progress bar.

Documentation
==============

You can read the rest of the documentation inside the docstrings.

Contributing 
=============
You can contribute to the project by reporting bugs, suggesting enhancements, or directly by extending and writing features (see the ongoing projects_).

.. _projects: https://github.com/mariostoev/finviz/projects/1

*You can also buy me a coffee!*

.. image:: https://user-images.githubusercontent.com/8982949/33011169-6da4af5e-cddd-11e7-94e5-a52d776b94ba.png
        :target: https://www.paypal.me/finvizapi

Disclaimer
-----------
*Using the library to acquire data from FinViz is against their Terms of Service and robots.txt. Use it responsibly and at your own risk. This library is built purely for educational purposes.*
