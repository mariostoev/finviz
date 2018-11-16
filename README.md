## finviz-api

`finviz-api` is compatible with Python 3.6+ only 

**What is Finviz?**

[Finviz.com](http://www.finviz.com) aims to make market information accessible and provides a lot of data in visual snapshots, allowing traders and investors to quickly find the stock, future or forex pair they are looking for. The site provides advanced screeners, market maps, analysis, comparative tools and charts.

### Important information

Any quotes data displayed on finviz.com is delayed by 15 minutes for NASDAQ, and 20 minutes for NYSE and AMEX. This API should **NOT** be used for live trading, it's main purpuse is financial analysis, research and data scraping.

### Using Screener()

    from finviz import Screener
    
    tickers = ['AAPL', 'ATVI', 'TSLA']
    filters = ['exch_nasd', 'cap_large']  # Shows companies in NASDAQ with Market Cap from $10bln. to $200bln.
    order = '-price'  # Orders the results by price descending
    rows = 37  # Collects the first 37 rows
    
    Screener(tickers, filters, order, quantity=elements)
    Screener.to_csv()
    
    # Creates screener_results.csv file in the current directory

Below, you can see all of the possible arguments that can be passed through Screener():

| Argument | Type | Example | Default |
| :---         |     :---:      |     :---:     |     :---:     |
| tickers  | list | ['AAPL', 'ATVI', 'TSLA']  | None |
| filters | list | ['exch_nasd', 'cap_large']  | None |
| order | string | '-price' | None |
| signal | string | 'ta_topgainers' | None |
| dir | string | 'C:/User/Desktop/data' | Current Directory |
| table | string | 'Performance' | 'Overview' |
| rows | int | 43 | Maximum |
