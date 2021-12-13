import json
import pathlib
import urllib.request
from urllib.parse import parse_qs as urlparse_qs
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup
from user_agent import generate_user_agent

import finviz.helper_functions.scraper_functions as scrape
from finviz.helper_functions.display_functions import create_table_string
from finviz.helper_functions.error_handling import InvalidTableType, NoResults
from finviz.helper_functions.request_functions import (Connector,
                                                       http_request_get,
                                                       sequential_data_scrape)
from finviz.helper_functions.save_data import export_to_csv, export_to_db

TABLE_TYPES = {
    "Overview": "111",
    "Valuation": "121",
    "Ownership": "131",
    "Performance": "141",
    "Custom": "152",
    "Financial": "161",
    "Technical": "171",
}


class Screener(object):
    """ Used to download data from https://www.finviz.com/screener.ashx. """

    @classmethod
    def init_from_url(cls, url, rows=None):
        """
        Initializes from url

        :param url: screener url
        :type url: string
        :param rows: total number of rows to get
        :type rows: int
        """

        split_query = urlparse_qs(urlparse(url).query)

        tickers = split_query["t"][0].split(",") if "t" in split_query else None
        filters = split_query["f"][0].split(",") if "f" in split_query else None
        custom = split_query["c"][0].split(",") if "c" in split_query else None
        order = split_query["o"][0] if "o" in split_query else ""
        signal = split_query["s"][0] if "s" in split_query else ""

        table = "Overview"
        if "v" in split_query:
            table_numbers_types = {v: k for k, v in TABLE_TYPES.items()}
            table_number_string = split_query["v"][0][0:3]
            try:
                table = table_numbers_types[table_number_string]
            except KeyError:
                raise InvalidTableType(split_query["v"][0])

        return cls(tickers, filters, rows, order, signal, table, custom)

    def __init__(
        self,
        tickers=None,
        filters=None,
        rows=None,
        order="",
        signal="",
        table=None,
        custom=None,
        user_agent=generate_user_agent(),
        request_method="sequential",
    ):
        """
        Initializes all variables to its values

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
        :param custom: collection of custom columns eg.: ['1', '21', '23', '45']
        :type custom: list
        :var self.data: list of dictionaries containing row data
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

        if table is None:
            self._table = "111"
        else:
            self._table = self.__check_table(table)

        if custom is None:
            self._custom = []
        else:
            self._table = "152"
            self._custom = custom

            if (
                "0" not in self._custom
            ):  # 0 (No.) is required for the sequence algorithm to work
                self._custom = ["0"] + self._custom

        self._rows = rows
        self._order = order
        self._signal = signal
        self._user_agent = user_agent
        self._request_method = request_method

        self.analysis = []
        self.data = self.__search_screener()

    def __call__(
        self,
        tickers=None,
        filters=None,
        rows=None,
        order="",
        signal="",
        table=None,
        custom=None,
    ):
        """
        Adds more filters to the screener. Example usage:

        stock_list = Screener(filters=['cap_large'])  # All the stocks with large market cap
        # After analyzing you decide you want to see which of the stocks have high dividend yield
        # and show their performance:
        stock_list(filters=['fa_div_high'], table='Performance')
        # Shows performance of stocks with large market cap and high dividend yield
        """

        if tickers:
            [self._tickers.append(item) for item in tickers]

        if filters:
            [self._filters.append(item) for item in filters]

        if table:
            self._table = self.__check_table(table)

        if order:
            self._order = order

        if signal:
            self._signal = signal

        if rows:
            self._rows = rows

        if custom:
            self._custom = custom

        self.analysis = []
        self.data = self.__search_screener()

    add = __call__

    def __str__(self):
        """ Returns a readable representation of a table. """

        table_list = [self.headers]

        for row in self.data:
            table_list.append([row[col] or "" for col in self.headers])

        return create_table_string(table_list)

    def __repr__(self):
        """ Returns a string representation of the parameter's values. """

        values = (
            f"tickers: {tuple(self._tickers)}\n"
            f"filters: {tuple(self._filters)}\n"
            f"rows: {self._rows}\n"
            f"order: {self._order}\n"
            f"signal: {self._signal}\n"
            f"table: {self._table}\n"
            f"table: {self._custom}"
        )

        return values

    def __len__(self):
        """ Returns an int with the number of total rows. """

        return int(self._rows)

    def __getitem__(self, position):
        """ Returns a dictionary containing specific row data. """

        return self.data[position]

    get = __getitem__

    @staticmethod
    def __check_table(input_table):
        """ Checks if the user input for table type is correct. Otherwise, raises an InvalidTableType error. """

        try:
            table = TABLE_TYPES[input_table]
            return table
        except KeyError:
            raise InvalidTableType(input_table)

    @staticmethod
    def load_filter_dict(reload=True):
        """
        Get dict of available filters. File containing json specification of filters will be built if it doesn't exist
        or if reload is False
        """

        # Get location of filter.json
        json_directory = pathlib.Path(__file__).parent
        json_file = pathlib.Path.joinpath(json_directory, "filters.json")

        # Reload the filters JSON file if present and requested
        if reload and json_file.is_file():
            with open(json_file, "r") as fp:
                return json.load(fp)

        # Get html from main filter page, ft=4 ensures all filters are present
        hdr = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) "
            "Chrome/23.0.1271.64 Safari/537.11"
        }
        url = "https://finviz.com/screener.ashx?ft=4"
        req = urllib.request.Request(url, headers=hdr)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode("utf-8")

        # Parse html and locate table we are interested in.
        # Use one of the text values and get the parent table from that
        bs = BeautifulSoup(html, "html.parser")
        filters_table = None
        for td in bs.find_all("td"):
            if td.get_text().strip() == "Exchange":
                filters_table = td.find_parent("table")
        if filters_table is None:
            raise Exception("Could not locate filter parameters")

        # Delete all div tags, we don't need them
        for div in filters_table.find_all("div"):
            div.decompose()

        # Populate dict with filtering options and corresponding filter tags
        filter_dict = {}
        td_list = filters_table.find_all("td")

        for i in range(0, len(td_list) - 2, 2):
            current_dict = {}
            if td_list[i].get_text().strip() == "":
                continue

            # Even td elements contain filter name (as shown on web page)
            filter_text = td_list[i].get_text().strip()

            # Odd td elements contain the filter tag and options
            selections = td_list[i + 1].find("select")
            filter_name = selections.get("data-filter").strip()

            # Store filter options for current filter
            options = selections.find_all("option", {"value": True})
            for opt in options:
                # Encoded filter string
                value = opt.get("value").strip()

                # String shown in pull-down menu
                text = opt.get_text()

                # Filter out unwanted items
                if value is None or "Elite" in text:
                    continue

                # Make filter string and store in dict
                current_dict[text] = f"{filter_name}_{value}"

            # Store current filter dict
            filter_dict[filter_text] = current_dict

        # Save filter dict to finviz directory
        try:
            with open(json_file, "w") as fp:
                json.dump(filter_dict, fp)
        except Exception as e:
            print(e)
            print("Unable to write to file{}".format(json_file))

        return filter_dict

    def to_sqlite(self, filename):
        """Exports the generated table into a SQLite database.

        :param filename: SQLite database file path
        :type filename: str
        """

        export_to_db(self.headers, self.data, filename)

    def to_csv(self, filename: str):
        """Exports the generated table into a CSV file.
        Returns a CSV string if filename is None.

        :param filename: CSV file path
        :type filename: str
        """

        if filename and filename.endswith(".csv"):
            filename = filename[:-4]

        if len(self.analysis) > 0:
            export_to_csv(
                [
                    "ticker",
                    "date",
                    "category",
                    "analyst",
                    "rating",
                    "price_from",
                    "price_to",
                ],
                self.analysis,
                f"{filename}-analysts.csv",
            )

        return export_to_csv(self.headers, self.data, f"{filename}.csv")

    def get_charts(self, period="d", size="l", chart_type="c", ta="1"):
        """
        Downloads the charts of all tickers shown by the table.

        :param period: table period eg. : 'd', 'w' or 'm' for daily, weekly and monthly periods
        :type period: str
        :param size: table size eg.: 'l' for large or 's' for small - choose large for better quality but higher size
        :type size: str
        :param chart_type: chart type: 'c' for candles or 'l' for lines
        :type chart_type: str
        :param ta: technical analysis eg.: '1' to show ta '0' to hide ta
        :type ta: str
        """

        encoded_payload = urlencode(
            {"ty": chart_type, "ta": ta, "p": period, "s": size}
        )

        sequential_data_scrape(
            scrape.download_chart_image,
            [
                f"https://finviz.com/chart.ashx?{encoded_payload}&t={row.get('Ticker')}"
                for row in self.data
            ],
            self._user_agent,
        )

    def get_ticker_details(self):
        """
        Downloads the details of all tickers shown by the table.
        """

        ticker_data = sequential_data_scrape(
            scrape.download_ticker_details,
            [
                f"https://finviz.com/quote.ashx?&t={row.get('Ticker')}"
                for row in self.data
            ],
            self._user_agent,
        )

        for entry in ticker_data:
            for key, value in entry.items():
                for ticker_generic in self.data:
                    if ticker_generic.get("Ticker") == key:
                        if "Sales" not in self.headers:
                            self.headers.extend(list(value[0].keys()))

                        ticker_generic.update(value[0])
                        self.analysis.extend(value[1])

        return self.data

    def __check_rows(self):
        """
        Checks if the user input for row number is correct.
        Otherwise, modifies the number or raises NoResults error.
        """

        self._total_rows = scrape.get_total_rows(self._page_content)

        if self._total_rows == 0:
            raise NoResults(self._url.split("?")[1])
        elif self._rows is None or self._rows > self._total_rows:
            return self._total_rows
        else:
            return self._rows

    def __get_table_headers(self):
        """ Private function used to return table headers. """

        return self._page_content.cssselect('tr[valign="middle"]')[0].xpath(
            "td//text()"
        )

    def __search_screener(self):
        """ Private function used to return data from the FinViz screener. """

        self._page_content, self._url = http_request_get(
            "https://finviz.com/screener.ashx",
            payload={
                "v": self._table,
                "t": ",".join(self._tickers),
                "f": ",".join(self._filters),
                "o": self._order,
                "s": self._signal,
                "c": ",".join(self._custom),
            },
            user_agent=self._user_agent,
        )

        self._rows = self.__check_rows()
        self.headers = self.__get_table_headers()

        if self._request_method == "async":
            async_connector = Connector(
                scrape.get_table,
                scrape.get_page_urls(self._page_content, self._rows, self._url),
                self._user_agent,
                self.headers,
                self._rows,
                css_select=True,
            )
            pages_data = async_connector.run_connector()
        else:
            pages_data = sequential_data_scrape(
                scrape.get_table,
                scrape.get_page_urls(self._page_content, self._rows, self._url),
                self._user_agent,
                self.headers,
                self._rows,
            )

        data = []
        for page in pages_data:
            for row in page:
                data.append(row)

        return data
