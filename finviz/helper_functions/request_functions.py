import asyncio
import time
from typing import Callable, Dict, List

import aiohttp
import requests
import urllib3
from lxml import html
from user_agent import generate_user_agent

from finviz.config import connection_settings
from finviz.helper_functions.error_handling import (ConnectionTimeout,
                                                    TooManyRequests)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def http_request_get(url, session=None, payload=None, parse=True):
    """ Sends a GET HTTP request to a website and returns its HTML content and full url address. """

    if payload is None:
        payload = {}

    try:
        if session:
            content = session.get(
                url,
                params=payload,
                verify=False,
                headers={"User-Agent": generate_user_agent()},
            )
        else:
            content = requests.get(
                url,
                params=payload,
                verify=False,
                headers={"User-Agent": generate_user_agent()},
            )

        content.raise_for_status()  # Raise HTTPError for bad requests (4xx or 5xx)
        if parse:
            return html.fromstring(content.text), content.url
        else:
            return content.text, content.url
    except (asyncio.TimeoutError, requests.exceptions.Timeout):
        raise ConnectionTimeout(url)


def sequential_data_scrape(
    scrape_func: Callable, urls: List[str], delay: float = 0.5, *args, **kwargs
) -> List[Dict]:
    data = []
    delay_multiplier = 1.0

    for url in urls:
        try:
            while True:
                response = requests.get(
                    url, headers={"User-Agent": generate_user_agent()}
                )
                if response.text == "Too many requests.":
                    time.sleep(delay * delay_multiplier)
                    delay_multiplier *= 1.5
                    continue
                else:
                    delay_multiplier = 1.0
                    break
            kwargs["URL"] = url
            data.append(scrape_func(response, *args, **kwargs))
            time.sleep(delay)
        except Exception as exc:
            raise exc

    return data


class Connector:
    """ Used to make asynchronous HTTP requests. """

    def __init__(
        self,
        scrape_function: Callable,
        urls: List[str],
        *args,
        css_select: bool = False
    ):
        self.scrape_function = scrape_function
        self.urls = urls
        self.arguments = args
        self.css_select = css_select
        self.data = []

    async def __http_request__async(
        self, url: str, session: aiohttp.ClientSession, user_agent: str
    ):
        """ Sends asynchronous http request to URL address and scrapes the webpage. """

        try:
            async with session.get(url, headers={"User-Agent": user_agent}) as response:
                page_html = await response.read()

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
        user_agent = generate_user_agent()

        async with aiohttp.ClientSession(
            connector=conn, timeout=timeout, headers={"User-Agent": user_agent}
        ) as session:
            for url in self.urls:
                async_tasks.append(self.__http_request__async(url, session, user_agent))

            self.data = await asyncio.gather(*async_tasks)

    def run_connector(self):
        """ Starts the asynchronous loop and returns the scraped data. """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__async_scraper())

        return self.data
