from finviz.helper_functions.request_functions import http_request_get

STOCK_URL = 'https://finviz.com/quote.ashx'
NEWS_URL = 'https://finviz.com/news.ashx'


def get_stock(ticker):
    """
    Returns a dictionary containing stock data.

    :param ticker: stock symbol
    :type ticker: str
    :return dict
    """

    data = {}
    page_parsed, _ = http_request_get(url=STOCK_URL, payload={'t': ticker}, parse=True)
    all_rows = [row.xpath('td//text()') for row in page_parsed.cssselect('tr[class="table-dark-row"]')]

    for row in all_rows:
        for column in range(0, 11):
            if column % 2 == 0:
                data[row[column]] = row[column + 1]

    return data


def get_insider(ticker):
    """
    Returns a list of dictionaries containing all recent insider transactions.

    :param ticker: stock symbol
    :return: list
    """

    page_parsed, _ = http_request_get(url=STOCK_URL, payload={'t': ticker}, parse=True)
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

    page_parsed, _ = http_request_get(url=STOCK_URL, payload={'t': ticker}, parse=True)
    all_news = page_parsed.cssselect('a[class="tab-link-news"]')
    headlines = [row.xpath('text()')[0] for row in all_news]
    urls = [row.get('href') for row in all_news]

    return list(zip(headlines, urls))


def get_all_news():
    """
    Returns a list of sets containing time, headline and url

    :return: list
    """

    page_parsed, _ = http_request_get(url=NEWS_URL, parse=True)
    all_dates = [row.text_content() for row in page_parsed.cssselect('td[class="nn-date"]')]
    all_headlines = [row.text_content() for row in page_parsed.cssselect('a[class="nn-tab-link"]')]
    all_links = [row.get('href') for row in page_parsed.cssselect('a[class="nn-tab-link"]')]

    return list(zip(all_dates, all_headlines, all_links))