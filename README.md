## finviz-api

`finviz-api` is compatible with Python 3 only 

**What is Finviz?**

[Finviz.com](http://www.finviz.com) aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools and charts.

### Installation

Install the current PyPi release by:

`pip install finviz`

Or install the development version from GitHub:

`pip install git+https://github.com/mariostoev/finviz-api`

### Important information

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpuse is financial analysis, research and data scraping.

### Using screener()

    from finviz import screener
    
    tickers = ['AAPL', 'ATVI', 'TSLA']
    filters = ['exch_nasd', 'cap_large']  # Shows companies in NASDAQ with Market Cap from $10bln. to $200bln.
    order = '-price'  # Orders the results by price descending
    elements = 100  # Scrape the first 100 elements only
    
    screener(tickers, filters, order, quantity=elements)
    
    # Returns a data.csv file containing the data from the screener

Below, you can see all of the possible arguments that can be passed through screener():

| Argument | Type | Example | Default |
| :---         |     :---:      |     :---:     |     :---:     |
| tickers  | list | ['AAPL', 'ATVI', 'TSLA']  | None |
| filters | list | ['exch_nasd', 'cap_large']  | None |
| order | string | '-price' | None |
| signal | string | 'ta_topgainers' | None |
| dir | string | 'C:/User/Desktop' | os.getcwd() |
| table | string | 'Performance' | 'Overview' |
| save_as | string | 'csv' | 'csv' |
| quantity | int | 50 | 20 |

### To do's:

- Use only aiohttp to make requests
- Remove warnings (unclosed connections)
- Add CSV, SQL and JSON support
- Integrate function to scrape each symbol individually
