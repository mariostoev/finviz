from finviz.config import connection_settings


class NoResults(Exception):
    """ Raise when there are no results found. """

    def __init__(self, query):
        super(NoResults, self).__init__(f"No results found for query: {query}")


class InvalidTableType(Exception):
    """ Raise when the given table type is invalid. """

    def __init__(self, arg):
        super(InvalidTableType, self).__init__(f"Invalid table type called: {arg}")


class TooManyRequests(Exception):
    """ Raise when HTTP request fails because too many requests were sent to FinViz at once. """

    def __init__(self, arg):
        super(TooManyRequests, self).__init__(f"Too many HTTP requests at once: {arg}")


class InvalidPortfolioID(Exception):
    """ Raise when the given portfolio id is invalid. """

    def __int__(self, portfolio_id):
        super(InvalidPortfolioID, self).__init__(
            f"Invalid portfolio with ID: {portfolio_id}"
        )


class NonexistentPortfolioName(Exception):
    """ Raise when the given portfolio name is nonexistent. """

    def __init__(self, name):
        super(NonexistentPortfolioName, self).__init__(
            f"Nonexistent portfolio with name: {name}"
        )


class NoPortfolio(Exception):
    """ Raise when the user has not created a portfolio. """

    def __int__(self, func_name):
        super(NoPortfolio, self).__init__(
            "Function ({func_name}) cannot be called because "
            "there is no existing portfolio."
        )


class InvalidTicker(Exception):
    """ Raise when the given ticker is nonexistent or unavailable on FinViz.  """

    def __init__(self, ticker):
        super(InvalidTicker, self).__init__(
            f"Unable to find {ticker} since it is non-existent or unavailable on FinViz."
        )


class ConnectionTimeout(Exception):
    """ The request has timed out while trying to connect to the remote server. """

    def __init__(self, webpage_link):
        super(ConnectionTimeout, self).__init__(
            f'Connection timed out after {connection_settings["CONNECTION_TIMEOUT"]} while trying to reach {webpage_link}'
        )
