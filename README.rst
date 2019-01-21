finviz-api
########
*Unofficial Python API for FinViz*

.. image:: https://badge.fury.io/py/finviz.svg
    :target: https://badge.fury.io/py/finviz
    
.. image:: https://img.shields.io/badge/python-3.6-blue.svg
    :target: https://www.python.org/downloads/release/python-360/
    
.. image:: https://img.shields.io/github/stars/mariostoev/finviz.svg
    :target: https://github.com/mariostoev/finviz/stargazers
    :alt: Stargazers
    
.. image:: https://pepy.tech/badge/finviz
    :target: https://pepy.tech/project/finviz
    
.. image:: http://hits.dwyl.io/mariostoev/finviz.svg
    :target: http://hits.dwyl.io/mariostoev/finviz

Installation
-----
The package has been uploaded to PyPi_, so you can install the latest release using:

.. _PyPi: https://pypi.org/project/finviz/

.. code:: bash

   $ pip install finviz

What is Finviz?
=====
FinViz_ aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools and charts.

.. _FinViz: https://finviz.com/

**Important Information**

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpuse is financial analysis, research and data scraping.

Using Screener
=====

.. code:: python

    from finviz.screener import Screener

    filters = ['exch_nasd', 'idx_sp500']  # Shows companies in NASDAQ which are in the S&P500
    # Get the first 50 results sorted by price ascending
    stock_list = Screener(filters=filters, order='price')

    # Export the screener results to .csv 
    stock_list.to_csv()

    # Create a SQLite database 
    stock_list.to_sqlite()

    for stock in stock_list[9:19]:  # Loop through 10th - 20th stocks 
        print(stock['Ticker'], stock['Price']) # Print symbol and price

    # Add more filters
    stock_list.add(filters=['fa_div_high'])  # Show stocks with high dividend yield
    # or just stock_list(filters=['fa_div_high'])

    # Print the table into the console
    print(stock_list)
    
.. image:: https://i.imgur.com/cb7UdxB.png

Using Portfolio
=====
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
    
Downloading charts
=====

.. code:: python
    
    # Monthly, Candles, Large, No Technical Analysis
    stock_list.get_charts(period='m', chart_type='c', size='l', ta=False)
    
    # period='d' > daily 
    # period='w' > weekly
    # period='m' > monthly
    
    # chart_type='c' > candle
    # chart_type='l' > lines
    
    # size='m' > small
    # size='l' > large
    
    # ta=True > display technical analysis
    # ta=False > ignore technical analysis
    

Documentation
=====

You can read the rest of the documentation inside the docstrings.

Contributing 
=====
You can contribute to the project by reporting bugs, suggesting enhancements, or directly by extending and writing features (see the ongoing projects_).

.. _projects: https://github.com/mariostoev/finviz/projects/1

*You can also buy me a coffee!*

.. image:: http://rickrduncan.com/wp-content/uploads/2017/11/buy-me-coffee-paypal.png
        :target: https://www.paypal.me/finvizapi
