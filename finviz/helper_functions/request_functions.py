import asyncio
import os
from typing import Callable, Dict, List

import aiohttp
import requests
import tenacity
import urllib3
from lxml import html
from requests import Response
from tqdm import tqdm
from user_agent import generate_user_agent

from finviz.config import connection_settings
from finviz.helper_functions.error_handling import ConnectionTimeout

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def http_request_get(
    url, session=None, payload=None, parse=True, user_agent=generate_user_agent()
):
    """ Sends a GET HTTP request to a website and returns its HTML content and full url address. """

    if payload is None:
        payload = {}

    try:
        if session:
            content = session.get(
                url,
                params=payload,
                verify=False,
                headers={"User-Agent": user_agent},
            )
        else:
            content = requests.get(
                url,
                params=payload,
                verify=False,
                headers={"User-Agent": user_agent},
            )

        content.raise_for_status()  # Raise HTTPError for bad requests (4xx or 5xx)
        if parse:
            return html.fromstring(content.text), content.url
        else:
            return content.text, content.url
    except (asyncio.TimeoutError, requests.exceptions.Timeout):
        raise ConnectionTimeout(url)


@tenacity.retry(wait=tenacity.wait_exponential())
def finviz_request(url: str, user_agent: str) -> Response:
    response = requests.get(url, headers={"User-Agent": user_agent})
    if response.text == "Too many requests.":
        raise Exception("Too many requests.")
    return response


def sequential_data_scrape(
    scrape_func: Callable, urls: List[str], user_agent: str, *args, **kwargs
) -> List[Dict]:
    data = []

    for url in tqdm(urls, disable="DISABLE_TQDM" in os.environ):
        try:
            response = finviz_request(url, user_agent)
            kwargs["URL"] = url
            data.append(scrape_func(response, *args, **kwargs))
        except Exception as exc:
            raise exc

    return data


class Connector:
    """ Used to make asynchronous HTTP requests. """

    def __init__(
        self,
        scrape_function: Callable,
        urls: List[str],
        user_agent: str,
        *args,
        css_select: bool = False
    ):
        self.scrape_function = scrape_function
        self.urls = urls
        self.user_agent = user_agent
        self.arguments = args
        self.css_select = css_select
        self.data = []

    async def __http_request__async(
        self,
        url: str,
        session: aiohttp.ClientSession,
    ):
        """ Sends asynchronous http request to URL address and scrapes the webpage. """

        try:
            async with session.get(
                url, headers={"User-Agent": self.user_agent}
            ) as response:
                page_html = await response.read()

                if page_html.decode("utf-8") == "Too many requests.":
                    raise Exception("Too many requests.")

                if self.css_select:
                    return self.scrape_function(
                        html.fromstring(page_html), *self.arguments
                    )
                return self.scrape_function(page_html, *self.arguments)
        except (asyncio.TimeoutError, requests.exceptions.Timeout):
            raise ConnectionTimeout(url)

    async def __async_scraper(self):
        """ Adds a URL's into a list of tasks and requests their response asynchronously. """

        async_tasks = []
        conn = aiohttp.TCPConnector(
            limit_per_host=connection_settings["CONCURRENT_CONNECTIONS"]
        )
        timeout = aiohttp.ClientTimeout(total=connection_settings["CONNECTION_TIMEOUT"])

        async with aiohttp.ClientSession(
            connector=conn, timeout=timeout, headers={"User-Agent": self.user_agent}
        ) as session:
            for url in self.urls:
                async_tasks.append(self.__http_request__async(url, session))

            self.data = await asyncio.gather(*async_tasks)

    def run_connector(self):
        """ Starts the asynchronous loop and returns the scraped data. """

        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__async_scraper())

        return self.data
