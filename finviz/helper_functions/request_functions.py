from finviz.helper_functions.error_handling import ConnectionTimeout
from finviz.config import connection_settings
from user_agent import generate_user_agent
from lxml import html
import asyncio
import aiohttp
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def http_request_get(url, session=None, payload=None, parse=True):
    """ Sends a GET HTTP request to a website and returns its HTML content and full url address. """

    if payload is None:
        payload = {}

    try:
        if session:
            content = session.get(url, params=payload, verify=False, headers={'User-Agent': generate_user_agent()})
        else:
            content = requests.get(url, params=payload, verify=False, headers={'User-Agent': generate_user_agent()})

        content.raise_for_status()  # Raise HTTPError for bad requests (4xx or 5xx)

        if parse:
            return html.fromstring(content.text), content.url
        else:
            return content.text, content.url
    except (asyncio.TimeoutError, requests.exceptions.Timeout):
        raise ConnectionTimeout(url)


class Connector(object):
    """ Used to make asynchronous HTTP requests. """

    def __init__(self, scrape_function, tasks, *args, cssselect=False):

        self.scrape_function = scrape_function
        self.tasks = tasks
        self.arguments = args
        self.cssselect = cssselect
        self.data = []

    async def __http_request__async(self, url, session):
        """ Sends asynchronous http request to URL address and scrapes the webpage. """

        try:
            async with session.get(url, headers={'User-Agent': generate_user_agent()}) as response:
                page_html = await response.read()

                if self.cssselect is True:
                    return self.scrape_function(html.fromstring(page_html), url=url, *self.arguments)
                else:
                    return self.scrape_function(page_html, url=url, *self.arguments)
        except (asyncio.TimeoutError, requests.exceptions.Timeout):
            raise ConnectionTimeout(url)

    async def __async_scraper(self):
        """ Adds a URL's into a list of tasks and requests their response asynchronously. """

        async_tasks = []
        conn = aiohttp.TCPConnector(limit_per_host=connection_settings['CONCURRENT_CONNECTIONS'])
        timeout = aiohttp.ClientTimeout(total=connection_settings['CONNECTION_TIMEOUT'])

        async with aiohttp.ClientSession(connector=conn,
                                         timeout=timeout,
                                         headers={'User-Agent': generate_user_agent()}) as session:
            for n in self.tasks:
                async_tasks.append(self.__http_request__async(n, session))

            self.data = await asyncio.gather(*async_tasks)

    def run_connector(self):
        """ Starts the asynchronous loop and returns the scraped data. """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__async_scraper())

        return self.data
