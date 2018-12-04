from finviz.request_functions import Connector, http_request
from .save_data import export_to_db, export_to_csv
from urllib.parse import urlencode
from lxml import html
from lxml import etree
import finviz.scraper_functions as scrape

# TODO > Add __add__ and __slice__(?) methods to the Screener class


class Screener(object):
    """ Used to download data from http://www.finviz.com/screener.ashx. """

    def __init__(self, tickers=None, filters=None, rows=None, order='', signal='', table='Overview'):
        """
        Initilizes all variables to its values

        :param tickers: collection of ticker strings eg.: ['AAPL', 'AMD', 'WMT']
        :type tickers: list
        :param filters: collection of filters strings eg.: ['exch_nasd', 'idx_sp500', 'fa_div_none']
        :type filters: list
        :param rows: total number of rows to get
        :type rows: int
        :param order: table order eg.: '-price' (to sort table by descending price)
        :type order: str
        :param signal: show by signal eg.: 'n_majornews' (for stocks with major news)
        :type signal: str
        :param table: table type eg.: 'Performance'
        :type table: str
        :var self.data: pages containing data about each row inside a dictionary
        :type self.data: list
        """

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

        self.data = self.__search_screener()

    def __repr__(self):
        """ Returns a string containing readable representation of a table. """

        table_string = ''
        table_list = [self._headers]

        for page in self.data:
            for row in page:
                table_list.append([str(row[col] or '') for col in self._headers])

        col_size = [max(map(len, col)) for col in zip(*table_list)]
        format_str = ' | '.join(["{{:<{}}}".format(i) for i in col_size])
        table_list.insert(1, ['-' * i for i in col_size])

        for item in table_list:
            table_string += format_str.format(*item) + '\n'

        return table_string

    def __len__(self):
        """ Returns an int with the number of total rows. """

        return int(self._rows)

    def to_sqlite(self):
        """ Exports the generated table into a SQLite database, located in the user's current directory. """

        export_to_db(self._headers, self.data)

    def to_csv(self):
        """ Exports the generated table into a CSV file, located in the user's current directory. """

        export_to_csv(self._headers, self.data)

    def get_charts(self, period='d', size='l', chart_type='c', ta='1'):
        """
        Downloads the charts of tickers shown by the table.

        :param period: table period eg. : 'd', 'w' or 'm' for daily, weekly and monthly periods
        :type period: str
        :param size: table size eg.: 'l' for large or 's' for small - choose large for better quality but higher size
        :type size: str
        :param chart_type: chart type: 'c' for candles or 'l' for lines
        :type chart_type: str
        :param ta: technical analysis eg.: '1' to show ta '0' to hide ta
        :type ta: str
        """

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

        async_connector = Connector(scrape.download_chart_image, chart_urls)
        async_connector.run_connector()

    def __get_table_headers(self):
        """ Private function used to return the table headers. """

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
        """ Private function used to return the table data from a single page. """

        def scrape_row(line):

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
                values = dict(zip(self._headers, scrape_row(row)))
                data_sets.append(values)
                break

            else:
                values = dict(zip(self._headers, scrape_row(row)))
                data_sets.append(values)

        return data_sets

    def __search_screener(self):
        """ Private function to return the data from the FinViz screener. """

        page_urls = scrape.get_page_urls(self._page_content, self._rows, self._url)
        async_connector = Connector(self.__get_table_data, page_urls)
        data = async_connector.run_connector()

        return data
