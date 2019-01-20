class NoResults(Exception):
    """ Raise when there are no results found. """

    def __init__(self, query):
        super(NoResults, self).__init__(f'No results found for query: {query}')


class InvalidTableType(Exception):
    """ Raise when the given table type is invalid. """

    def __init__(self, arg):
        super(InvalidTableType, self).__init__(f'Invalid table type called: {arg}')


class InvalidPortfolioID(Exception):
    """ Rasie when the given portfolio id is invalid. """

    def __int__(self, portfolio_id):
        super(InvalidPortfolioID, self).__init__(f'Invalid portfolio with ID: {portfolio_id}')


class UnexistingPortfolioName(Exception):
    """ Raise when the given portfolio name is unexisting. """

    def __init__(self, name):
        super(UnexistingPortfolioName, self).__init__(f'Unexisting portfolio with name: {name}')


class NoPortfolio(Exception):
    """ Raise when the user has not created a portfolio. """

    def __int__(self, func_name):
        super(NoPortfolio, self).__init__("Function ({func_name}) cannot be called because "
                                          "there is no existing portfolio.")
