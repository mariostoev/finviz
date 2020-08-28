import finviz
import json
from get_all_tickers.get_tickers import get_tickers

tickers = get_tickers(NYSE=True, NASDAQ=True, AMEX=True)
# print(tickers)

# data = {'col1': [1, 2], 'col2': [3, 4]}

for ticker in tickers:
    # if ticker == "TSLA":
    print(f'ticker-{ticker}')
    stock = finviz.get_stock('AAPL')
    targets = finviz.get_analyst_price_targets('AAPL')
    print(json.dumps(targets, indent=4))
    break
# data = finviz.get_news('AAPL')

# with open('finnviz-news.json', 'w') as outfile:
#     json.dump(data, outfile, indent=4)