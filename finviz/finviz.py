from urllib.request import urlopen
from bs4 import BeautifulSoup
from table_format import table_format
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


def httprequest(payload):
    payload['user-agent'] = '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36
                            (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'''
    request = requests.get('https://finviz.com/screener.ashx', params=payload)

    return request.url


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

    requestUrl = httprequest(payload)
    html = urllib.request.Request(requestUrl)
    content = urlopen(html).read()
    pageContent = BeautifulSoup(content, 'html.parser')
    pageContent.find('table', {'bgcolor': 'd3d3d3'})

    headers = [i for i in table_format[TABLE[table][1]]]
    datasets = []

    for row in pageContent.findAll('tr', {'valign': 'top'})[1:]:
        values = dict(zip(headers, (href.text for href in row.findAll('a'))))
        datasets.append(values)

    print(datasets)

screener(filters=['cap_microunder' , 'exch_nasd' , 'sh_avgvol_u50' , 'sh_relvol_o2'])