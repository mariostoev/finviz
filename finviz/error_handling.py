class NoResults(Exception):
    """ Raise when there are no results found. """

    def __init__(self, query):
        self.query = query
        super(NoResults, self).__init__(f"No results found for query: {query}")


class InvalidTableType(Exception):
    """ Raise when the given table type is invalid. """

    def __init__(self, arg):
        self.arg = arg
        super(InvalidTableType, self).__init__(f"Invalid table type called: {arg}")
