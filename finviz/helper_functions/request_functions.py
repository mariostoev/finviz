import asyncio
import os
import random
import time
from typing import Callable, Dict, List, Final, Optional

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


# List of user agents for rotation
USER_AGENTS: Final = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15",
]

@tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10))
def finviz_request(url: str, user_agent: str) -> requests.Response:
    response = requests.get(url, headers={"User-Agent": user_agent})
    if response.text == "Too many requests.":
        raise Exception("Too many requests.")
    return response

def sequential_data_scrape(
    scrape_func: Callable, urls: List[str], user_agent: Optional[str], *args, **kwargs
) -> List[Dict]:
    data = []

    for url in tqdm(urls, disable="DISABLE_TQDM" in os.environ):
        user_agent = random.choice(USER_AGENTS) if not user_agent else user_agent  # Rotate user agents
        try:
            response = finviz_request(url, user_agent)
            kwargs["URL"] = url
            data.append(scrape_func(response, *args, **kwargs))
            time.sleep(random.uniform(1, 3))  # Add a random delay between requests
        except Exception as exc:
            print(f"Error fetching {url}: {exc}")
            continue  # Skip this URL and move to the next one

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
