from finviz.request_functions import Connector, http_request
from .save_data import export_to_db, export_to_csv
from urllib.parse import urlencode
from lxml import html
from lxml import etree
import finviz.scraper_functions as scrape


class Screener(object):

    def __init__(self, tickers=None, filters=None, rows=None, order='', signal='', table='Overview'):

        if tickers is None:
            self._tickers = []
        else:
            self._tickers = tickers

        if filters is None:
            self._filters = []
        else:
            self._filters = filters

        self._table_types = {
            'Overview': '110',
            'Valuation': '120',
            'Ownership': '130',
            'Performance': '140',
            'Custom': '150',
            'Financial': '160',
            'Technical': '170'
        }

        self._page_unparsed, self._url = http_request('https://finviz.com/screener.ashx', payload={
                                                   'v': self._table_types[table],
                                                   't': ','.join(self._tickers),
                                                   'f': ','.join(self._filters),
                                                   'o': order,
                                                   's': signal
                                                   })

        self._page_content = html.fromstring(self._page_unparsed)
        self._headers = self.__get_table_headers()

        if rows is None:
            self._rows = scrape.get_total_rows(self._page_content)
        else:
            self._rows = rows

        self.data = None
        self.__search_screener()

    def to_sqlite(self):
        export_to_db(self._headers, self.data)

    def to_csv(self):
        export_to_csv(self._headers, self.data)

    def get_charts(self, period='d', size='l', chart_type='c', ta='1'):

        """ Asynchronously downloads charts of tickers displayed by the screener. """

        payload = {
            'ty': chart_type,
            'ta': ta,
            'p': period,
            's': size
        }

        base_url = 'https://finviz.com/chart.ashx?' + urlencode(payload)
        chart_urls = []

        for page in self.data:
            for row in page:
                chart_urls.append(base_url + '&t={}'.format(row.get('Ticker')))

        async_connector = Connector(scrape.download_image, chart_urls)
        async_connector.run_connector()

    def __get_table_headers(self):

        """ Scrapes the table headers from the initial page. """

        first_row = self._page_content.cssselect('tr[valign="middle"]')

        headers = []
        for table_content in first_row[0]:

            if table_content.text is None:
                sorted_text_list = etree.tostring(table_content.cssselect('img')[0]).decode("utf-8").split('/>')
                headers.append(sorted_text_list[1])
            else:
                headers.append(table_content.text)

        return headers

    def __get_table_data(self, page=None, url=None):

        """ Returns the data, from each row of the table, inside a dictionary ."""

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

            if int(row[0].text) is self._rows:
                values = dict(zip(self._headers, parse_row(row)))
                data_sets.append(values)
                break

            else:
                values = dict(zip(self._headers, parse_row(row)))
                data_sets.append(values)

        return data_sets

    def __search_screener(self):

        """ Saves data from the FinViz screener. """

        page_urls = scrape.get_page_urls(self._page_content, self._rows, self._url)
        async_connector = Connector(self.__get_table_data, page_urls)
        self.data = async_connector.run_connector()
