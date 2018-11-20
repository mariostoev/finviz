from lxml import html
from lxml import etree
import finviz.request_functions as send
import finviz.scraper_functions as scrape
import requests
import urllib3
import os
from .save_data import export_to_csv, export_to_db, select_from_db


class Screener(object):

    def __init__(self, tickers=None, filters=None, order='', rows=None, signal='', table='Overview'):

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

        if directory is None:

            import os
            directory = os.getcwd()

        export_to_csv(self.headers, self.data, directory)

    def to_db(self):
        export_to_db(self.headers, self.data)

    def from_db(self):
        select_from_db()

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

        table = {
            'Overview': '110',
            'Valuation': '120',
            'Ownership': '130',
            'Performance': '140',
            'Custom': '150',
            'Financial': '160',
            'Technical': '170'
        }

        payload = {
            'v': table[self.table],
            't': ','.join(self.tickers),
            'f': ','.join(self.filters),
            'o': self.order,
            's': self.signal
        }

        self.page_content, self.url = send.http_request('https://finviz.com/screener.ashx', payload)
        self.page_content = html.fromstring(self.page_content.text)  # Parses the page with the default lxml parser

        self.__get_table_headers()

        if self.rows is None:
            self.rows = scrape.get_total_rows(self.page_content)

        self.page_urls = scrape.get_page_urls(self.page_content, self.rows, self.url)

        async_connector = send.Connector(self.__get_table_data, self.page_urls)
        self.data = async_connector.run_connector()
