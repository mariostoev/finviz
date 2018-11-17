from finviz.async_connector import Connector
from lxml import html
from lxml import etree
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TABLE = {
    'Overview': '110',
    'Valuation': '120',
    'Ownership': '130',
    'Performance': '140',
    'Custom': '150',
    'Financial': '160',
    'Technical': '170'
}


def http_request(url, payload=None):

    if payload is None:
        payload = {}

    content = requests.get(url, params=payload, verify=False)
    content.raise_for_status()  # Raise HTTPError for bad requests (4xx or 5xx)

    return content, content.url


class Screener(object):

    def __init__(self, tickers=None, filters=None, rows=None, order='', signal='', table='Overview'):

        if tickers is None:
            self.tickers = []
        else:
            self.tickers = tickers

        if filters is None:
            self.filters = []
        else:
            self.filters = filters

        self.rows = rows
        self.order = order
        self.signal = signal
        self.table = table
        self.page_content = None
        self.url = None
        self.headers = None
        self.page_urls = None
        self.data = None

        self.__search_screener()

    def to_csv(self, directory=None):

        from save_data import export_to_csv

        if directory is None:
            directory = os.getcwd()

        export_to_csv(self.headers, self.data, directory)

    def __get_total_rows(self):

        total_element = self.page_content.cssselect('td[width="140"]')
        self.rows = int(etree.tostring(total_element[0]).decode("utf-8").split('</b>')[1].split(' ')[0])

    def __get_page_urls(self):

        try:
            total_pages = int([i.text.split('/')[1] for i in self.page_content.cssselect('option[value="1"]')][0])
        except IndexError:  # No results found
            return None

        urls = []

        for page_number in range(1, total_pages + 1):

            sequence = 1 + (page_number - 1) * 20

            if sequence - 20 <= self.rows < sequence:
                break
            else:
                urls.append(self.url + '&r={}'.format(str(sequence)))

        self.page_urls = urls

    def __get_table_headers(self):

        first_row = self.page_content.cssselect('tr[valign="middle"]')

        headers = []
        for table_content in first_row[0]:

            if table_content.text is None:
                sorted_text_list = etree.tostring(table_content.cssselect('img')[0]).decode("utf-8").split('/>')
                headers.append(sorted_text_list[1])
            else:
                headers.append(table_content.text)

        self.headers = headers

    def __get_table_data(self, page=None):

        def parse_row(line):

            row_data = []

            for tags in line:
                if tags.text is not None:
                    row_data.append(tags.text)
                else:
                    row_data.append([span.text for span in tags.cssselect('span')][0])

            return row_data

        data_sets = []
        page = html.fromstring(page)
        all_rows = [i.cssselect('a') for i in page.cssselect('tr[valign="top"]')[1:]]

        for row in all_rows:

            if int(row[0].text) is self.rows:
                values = dict(zip(self.headers, parse_row(row)))
                data_sets.append(values)
                break

            else:
                values = dict(zip(self.headers, parse_row(row)))
                data_sets.append(values)

        return data_sets

    def __search_screener(self):

        payload = {
            'v': TABLE[self.table],
            't': ','.join(self.tickers),
            'f': ','.join(self.filters),
            'o': self.order,
            's': self.signal
        }

        self.page_content, self.url = http_request('https://finviz.com/screener.ashx', payload)
        self.page_content = html.fromstring(self.page_content.text)  # Parses the page with the default lxml parser

        self.__get_table_headers()

        if self.rows is None:
            self.__get_total_rows()

        self.__get_page_urls()

        if self.page_urls is None:
            raise Exception("No results matching the criteria: {}"
                            .format(self.url.split('?', 1)[1]))

        async_connector = Connector(self.__get_table_data, self.page_urls)
        self.data = async_connector.run_connector()
