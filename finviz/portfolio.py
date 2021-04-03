import csv

import requests
from lxml import html
from user_agent import generate_user_agent

from finviz.helper_functions.display_functions import create_table_string
from finviz.helper_functions.error_handling import (InvalidPortfolioID,
                                                    InvalidTicker,
                                                    NonexistentPortfolioName)
from finviz.helper_functions.request_functions import http_request_get
from finviz.helper_functions.scraper_functions import get_table

LOGIN_URL = "https://finviz.com/login_submit.ashx"
PRICE_REQUEST_URL = "https://finviz.com/request_quote.ashx"
PORTFOLIO_URL = "https://finviz.com/portfolio.ashx"
PORTFOLIO_SUBMIT_URL = "https://finviz.com/portfolio_submit.ashx"
PORTFOLIO_DIGIT_COUNT = 9  # Portfolio ID is always 9 digits
PORTFOLIO_HEADERS = [
    "No.",
    "Ticker",
    "Company",
    "Price",
    "Change%",
    "Volume",
    "Transaction",
    "Date",
    "Shares",
    "Cost",
    "Market Value",
    "Gain$",
    "Gain%",
    "Change$",
]


class Portfolio(object):
    """ Used to interact with FinViz Portfolio. """

    def __init__(self, email, password, portfolio=None):
        """
        Logs in to FinViz and send a GET request to the portfolio.
        """

        payload = {"email": email, "password": password}

        # Create a session and log in by sending a POST request
        self._session = requests.session()
        auth_response = self._session.post(
            LOGIN_URL, data=payload, headers={"User-Agent": generate_user_agent()}
        )

        if not auth_response.ok:  # If the post request wasn't successful
            auth_response.raise_for_status()

        # Get the parsed HTML and the URL of the base portfolio page
        self._page_content, self.portfolio_url = http_request_get(
            url=PORTFOLIO_URL, session=self._session, parse=False
        )

        # If the user has not created a portfolio it redirects the request to <url>?v=2)
        self.created = True
        if self.portfolio_url == f"{PORTFOLIO_URL}?v=2":
            self.created = False

        if self.created:
            if portfolio:
                self._page_content, _ = self.__get_portfolio_url(portfolio)

            self.data = get_table(self._page_content, PORTFOLIO_HEADERS)

    def __str__(self):
        """ Returns a readable representation of a table. """

        table_list = [PORTFOLIO_HEADERS]

        for row in self.data:
            table_list.append([row[col] or "" for col in PORTFOLIO_HEADERS])

        return create_table_string(table_list)

    def create_portfolio(self, name, file, drop_invalid_ticker=False):
        """
        Creates a new portfolio from a .csv file.

        The .csv file must be in the following format:
        Ticker,Transaction,Date,Shares,Price
        NVDA,2,14-04-2018,43,148.26
        AAPL,1,01-05-2019,12
        WMT,1,25-02-2015,20
        ENGH:CA,1,,1,

        (!) For transaction - 1 = BUY, 2 = SELL
        (!) Note that if the price is omitted the function will take today's ticker price
        """

        data = {
            "portfolio_id": "0",
            "portfolio_name": name,
        }

        with open(file, "r") as infile:
            reader = csv.reader(infile)
            next(reader, None)  # Skip the headers

            for row_number, row in enumerate(reader, 0):
                row_number_string = str(row_number)
                data["ticker" + row_number_string] = row[0]
                data["transaction" + row_number_string] = row[1]
                data["date" + row_number_string] = row[2]
                data["shares" + row_number_string] = row[3]

                try:
                    # empty string is no price, so try get today's price
                    assert data["price" + row_number_string] != ""
                    data["price" + row_number_string] = row[4]
                except (IndexError, KeyError):
                    current_price_page, _ = http_request_get(
                        PRICE_REQUEST_URL, payload={"t": row[0]}, parse=True
                    )

                    # if price not available on finviz don't upload that ticker to portfolio
                    if current_price_page.text == "NA":
                        if not drop_invalid_ticker:
                            raise InvalidTicker(row[0])
                        del data["ticker" + row_number_string]
                        del data["transaction" + row_number_string]
                        del data["date" + row_number_string]
                        del data["shares" + row_number_string]
                    else:
                        data["price" + row_number_string] = current_price_page.text
        self._session.post(PORTFOLIO_SUBMIT_URL, data=data)

    def __get_portfolio_url(self, portfolio_name):
        """ Private function used to return the portfolio url from a given id/name. """

        # If the user has provided an ID (Portfolio ID is always an int)
        if isinstance(portfolio_name, int):
            # Raise error for invalid portfolio ID
            if not len(str(portfolio_name)) == PORTFOLIO_DIGIT_COUNT:
                raise InvalidPortfolioID(portfolio_name)
            else:
                return http_request_get(
                    url=f"{PORTFOLIO_URL}?pid={portfolio_name}",
                    session=self._session,
                    parse=False,
                )
        else:  # else the user has passed a name
            # We remove the first element, since it's redundant
            for portfolio in html.fromstring(self._page_content).cssselect("option")[
                1:
            ]:
                if portfolio.text == portfolio_name:
                    return http_request_get(
                        url=f"{PORTFOLIO_URL}?pid={portfolio.get('value')}",
                        session=self._session,
                        parse=False,
                    )
            # Raise Non-existing PortfolioName if none of the names match
            raise NonexistentPortfolioName(portfolio_name)
