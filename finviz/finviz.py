from urllib.request import urlopen
from lxml import html
from table_format import table_format
import asyncio
import aiohttp
import urllib
import requests
import os

TABLE = {
    'Overview': ['110', 0],
    'Valuation': ['120', 1],
    'Ownership': ['130', 2],
    'Performance': ['140', 3],
    'Custom': ['150', 4],
    'Financial': ['160', 5],
    'Technical': ['170', 7]
}


def parse(url):

    """
    Returns the html content of a web page.
    """

    request = urllib.request.Request(url)
    html = urlopen(request).read()
    pageContent = html.fromstring(content)

    return pageContent


def httprequest(payload):
    
    """
    Parses the url by given parameters and sends
    request to the website.
    """

    payload['user-agent'] = '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36
                            (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'''
    request = requests.get('https://finviz.com/screener.ashx', params=payload)

    return request.url


def page(url, quantity):

    """
    Returns a list with the URL's of the all pages and
    the headers of the table.
    """

    pageContent = parse(url)

    try:
        total_pages = int([i.text.split('/')[1] for i in pageContent.cssselect('option[value="1"]')][0])
    except AttributeError:  # No results found
        return None

    URLS = []
    # Using basic level arithmetic sequence to fetch urls
    for i in range(1, total_pages + 1):
        sequence = 1 + (i - 1) * 20
        if sequence - 20 <= quantity < sequence:  # PROBLEM WITH QUANTITY = 1
            break
        else:
            URLS.append(url + '&r={}'.format(str(sequence)))

    return URLS


def parse_row(row):

    """
    Scrapes each element in a row
    """

    row_data = []

    for tags in row:
        if tags.text is not None:
            row_data.append(tags.text)
        else:
            row_data.append([span.text for span in tags.cssselect('span')][0])

    return row_data


def get_data(html, headers, quantity):

    """
    Iterates over the screener's table and saves each
    row's data into a dictionary.
    """
    
    datasets = []
    pageContent = html.fromstring(content)
    all_rows = [i.cssselect('a') for i in pageContent.cssselect('tr[valign="top"]')[1:]]

    for row in all_rows:
        if int(row[0].text) is quantity:
            values = dict(zip(table_format[0], parse_row(row)))
            datasets.append(values)
            break
        else:
            values = dict(zip(table_format[0], parse_row(row)))
            datasets.append(values)

    return datasets


def screener(tickers=[], filters=[], order='',
             signal='', todir=os.getcwd(), table='Overview',
             export='sql', quantity=20):

    """
    With given specific filters, screener() scrapes table data
    from Finviz and creates a file containing all of
    the information.
    """

    payload = {
        'v': TABLE[table][0],  # Overview search
        't': ','.join(tickers),
        'f': ','.join(filters),
        'o': order,
        's': signal
    }

    headers = [i for i in table_format[TABLE[table][1]]]
    URLS = page(http_request(payload), quantity)
    DATA = []

    async def get_page(url):
        session = aiohttp.ClientSession()
        response = yield from aiohttp.request('GET', url, compress=True)
        session.close()
        return (yield from response.text())

    async def print_data(url, headers, quantity):
        page = yield from get_page(url)
        data = get_data(page, headers, quantity)
        DATA.append(data)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([print_data(i, headers, quantity) for i in URLS]))

    return DATA
