from urllib.request import urlopen
from bs4 import BeautifulSoup
from table_format import table_format
import urllib
import requests
import os

TABLE = {
    'Overview': '110,0',
    'Valuation': '120,1',
    'Ownership': '130,2',
    'Performance': '140,3',
    'Custom': '150,4',
    'Financial': '160,5',
    'Technical': '170,6'
}

DATA = {}


def httprequest(payload):
    payload['user-agent'] = '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36
                            (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'''
    request = requests.get('https://finviz.com/screener.ashx', params=payload)

    return request.url

def screener(tickers=[], filters=[], order='',
            signal='', dir=os.getcwd(), table='Overview',
            quantity=20):

    """
    With given specefic filters, screener() scrapes table data
    from Finviz and creates a file containing all of
    the information.
    """

    payload = {
        'v': TABLE[table].split(',')[0],  # Overview search
        't': ','.join(tickers),
        'f': ','.join(filters),
        'o': order,
        's': signal
    }

    requestUrl = httprequest(payload)
    html = urllib.request.Request(requestUrl)
    content = urlopen(html).read()
    pageContent = BeautifulSoup(content, 'html.parser')

    for bodyContent in pageContent('table', {'bgcolor': '#d3d3d3'}):
        for row in bodyContent.findAll('tr')[1:]:
            data = []
            for href in row.findAll('a'):
                data.append(href.Text)
                print(href.text)

                if len(data) == len(table_format[int(TABLE[table].split(',')[1])]):
                    print('=======')





screener()
