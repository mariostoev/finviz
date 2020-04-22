from finviz.helper_functions.request_functions import http_request_get
from finviz.helper_functions.scraper_functions import get_table
from finviz.helper_functions.save_data import STOCK_PAGE

import datetime

STOCK_URL = 'https://finviz.com/quote.ashx'
NEWS_URL = 'https://finviz.com/news.ashx'
CRYPTO_URL = 'https://finviz.com/crypto_performance.ashx'


def get_page(ticker):
    global STOCK_PAGE

    if ticker not in STOCK_PAGE:
        STOCK_PAGE[ticker], _ = http_request_get(url=STOCK_URL, payload={'t': ticker}, parse=True)


def get_stock(ticker):
    """
    Returns a dictionary containing stock data.

    :param ticker: stock symbol
    :type ticker: str
    :return dict
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]

    title = page_parsed.cssselect('table[class="fullview-title"]')[0]
    keys = ['Company', 'Sector', 'Industry', 'Country']
    fields = [f.text_content() for f in title.cssselect('a[class="tab-link"]')]
    data = dict(zip(keys, fields))

    all_rows = [row.xpath('td//text()') for row in page_parsed.cssselect('tr[class="table-dark-row"]')]

    for row in all_rows:
        for column in range(0, 11, 2):
            data[row[column]] = row[column + 1]

    return data


def get_insider(ticker):
    """
    Returns a list of dictionaries containing all recent insider transactions.

    :param ticker: stock symbol
    :return: list
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]
    table = page_parsed.cssselect('table[class="body-table"]')[0]
    headers = table[0].xpath('td//text()')
    data = [dict(zip(headers, row.xpath('td//text()'))) for row in table[1:]]

    return data


def get_news(ticker):
    """
    Returns a list of sets containing news headline and url

    :param ticker: stock symbol
    :return: list
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]
    all_news = page_parsed.cssselect('a[class="tab-link-news"]')
    headlines = [row.xpath('text()')[0] for row in all_news]
    urls = [row.get('href') for row in all_news]

    return list(zip(headlines, urls))


def get_all_news():
    """
    Returns a list of sets containing time, headline and url

    :return: list
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]
    all_dates = [row.text_content() for row in page_parsed.cssselect('td[class="nn-date"]')]
    all_headlines = [row.text_content() for row in page_parsed.cssselect('a[class="nn-tab-link"]')]
    all_links = [row.get('href') for row in page_parsed.cssselect('a[class="nn-tab-link"]')]

    return list(zip(all_dates, all_headlines, all_links))


def get_crypto(pair):
    """

    :param pair: crypto pair
    :return: dictionary
    """

    page_parsed, _ = http_request_get(url=CRYPTO_URL, parse=True)
    page_html, _ = http_request_get(url=CRYPTO_URL, parse=False)
    crypto_headers = page_parsed.cssselect('tr[valign="middle"]')[0].xpath('td//text()')
    crypto_table_data = get_table(page_html, crypto_headers)

    return crypto_table_data[pair]


def get_analyst_price_targets(ticker):
    """
    Returns a list of dictionaries containing all analyst ratings and Price targets
     - if any of 'price_from' or 'price_to' are not available in the DATA, then those values are set to default 0
    :param ticker: stock symbol
    :return: list
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]
    table = page_parsed.cssselect('table[class="fullview-ratings-outer"]')[0]
    ratings_list = [row.xpath('td//text()') for row in table]
    ratings_list = [[val for val in row if val != '\n'] for row in ratings_list] #remove new line entries

    headers = ['date', 'category', 'analyst', 'rating', 'price_from', 'price_to'] # header names
    analyst_price_targets = []

    for row in ratings_list:
        price_from, price_to = 0, 0  # defalut values for len(row) == 4 , that is there is NO price information
        if len(row) == 5:
            strings = row[4].split('→')
            #print(strings)
            if len(strings) == 1:
                price_to = int(strings[0].strip(' ').strip('$'))   # if only ONE price is avalable then it is 'price_to' value
            else:
                price_from = int(strings[0].strip(' ').strip('$'))  # both '_from' & '_to' prices available
                price_to = int(strings[1].strip(' ').strip('$'))

        elements = row[:4]  # only take first 4 elements, discard last element if exists
        elements.append(price_from)
        elements.append(price_to)
        elements[0] = datetime.datetime.strptime(elements[0], '%b-%d-%y').strftime('%Y-%m-%d') # convert date format
        data = dict(zip(headers, elements))
        analyst_price_targets.append(data)

    return analyst_price_targets
