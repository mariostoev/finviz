import asyncio
import aiohttp
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def http_request(url, payload=None):
    """ Makes a HTTP request to a website and returns its HTML content and full url address. """

    if payload is None:
        payload = {}

    content = requests.get(url, params=payload, verify=False)
    content.raise_for_status()  # Raise HTTPError for bad requests (4xx or 5xx)

    return content.text, content.url


class Connector(object):
    """ Used to make asynchronous HTTP requests. """

    def __init__(self, scrape_function, tasks):

        self.scrape_function = scrape_function
        self.tasks = tasks
        self.data = []

    async def __http_request__async(self, url, session):
        """ Sends asynchronous http request to URL address and scrapes the webpage. """

        async with session.get(url) as response:
            page_html = await response.read()

            return self.scrape_function(page_html, url)

    async def __async_scraper(self):
        """ Adds a URL's into a list of tasks and requests their response asynchronously. """

        async_tasks = []
        async with aiohttp.ClientSession() as session:
            for n in self.tasks:
                async_tasks.append(self.__http_request__async(n, session))

            self.data = await asyncio.gather(*async_tasks)

    def run_connector(self):
        """ Starts the asynchronous loop and returns the scraped data. """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__async_scraper())

        return self.data
