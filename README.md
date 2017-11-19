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

### Notes on performance

The API uses various modules to obtain and format data, thus resulting in a slight decrease of performance. Although that is barely noticable, the bottleneck will be partly, if not entirely based on your internet speed. After the last update I've come to the conclusion to stop optimizing the scraping algorithm and focus on data storage. 

### To do's:

Recently I've settled with an issue regarding using JSON files to store data. I decided that the JSON format is not the corrent database to store this type of information (talking about the screener here). Furthermore, continuing to add new features to the API I'll open mindedly research various types of databases, while looking to implement JSON support. 
