## finviz-api

`finviz-api` is compatible with Python 3 only 

**What is finviz?**

Finviz aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools and charts.

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
    
    screener(tickers, filters, order)
    
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

### Performance

As of the latest update, after trial and error, I'll stop attempting to improve the performance of the scraper. Each command takes around 4 seconds to execute, and I've come to the conclusion that CPU performance is not the bottleneck here, but the internet speed. That means the time to complete each request to screener() will vary on your download speed.

### To do's:

- Limit the quantity of results saved from screener()
- Add CSV and SQL support
- Obtain information from the homepage
- Scrape data from individual symbol page
