class NoResults(Exception):
    """ Raise when there are no results found. """

    def __init__(self, query):
        self.query = query
        super(NoResults, self).__init__("No results found for query: {}".format(query))


class InvalidTableType(Exception):
    """ Raise when the given table type is invalid. """

    def __init__(self, arg):
        self.arg = arg
        super(InvalidTableType, self).__init__("Invalid table type called: {}".format(arg))
