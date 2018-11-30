## finviz-api

[![PyPI version](https://badge.fury.io/py/finviz.svg)](https://badge.fury.io/py/finviz)
[![GitHub stars](https://img.shields.io/github/stars/mariostoev/finviz.svg)](https://github.com/mariostoev/finviz/stargazers)
[![Downloads](https://pepy.tech/badge/finviz)](https://pepy.tech/project/finviz)
[![HitCount](http://hits.dwyl.io/mariostoev/finviz.svg)](http://hits.dwyl.io/mariostoev/finviz)


`finviz` is compatible with Python 3.5+ only 

**What is Finviz?**

[Finviz.com](http://www.finviz.com) aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools and charts.

### Important information

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpuse is financial analysis, research and data scraping.

### Install the current release using PyPi

    pip install finviz

### Using Screener()

    from finviz.screener import Screener
    
    filters = ['exch_nasd', 'cap_large']  # Shows companies in NASDAQ with a market cap from $10bln. to $200bln.
    order = '-price'  # Orders the results by price descending

    stocks = Screener(filters, order, rows=50)  # Get the first 50 results
    
    # Export the screener results to .csv 
    stocks.to_csv()
    
    # Create a SQLite database 
    stocks.to_sqlite()
    
### Download results as a chart

    stocks.get_charts(period='m', chart_type='c', size='l', ta=False)  # Monthly, Candles, Large, No Technical Analysis
    
    # period='d' > daily 
    # period='w' > weekly
    # period='m' > monthly
    
    # chart_type='c' > candle
    # chart_type='l' > lines
    
    # size='m' > small
    # size='l' > large
    
    # ta=True > display technical analysis
    # ta=False > ignore technical analysis



Below, you can see all of the possible arguments that can be passed through Screener():

| Argument | Type | Example | Default |
| :---         |     :---:      |     :---:     |     :---:     |
| tickers  | list | ['AAPL', 'ATVI', 'TSLA']  | None |
| filters | list | ['exch_nasd', 'cap_large']  | None |
| order | string | '-price' | None |
| signal | string | 'ta_topgainers' | None |
| table | string | 'Performance' | 'Overview' |
| rows | string | 43 | Maximum |

