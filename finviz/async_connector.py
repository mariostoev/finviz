import asyncio
import aiohttp


class Connector(object):

    def __init__(self, scrape_function, tasks):

        self.scrape_function = scrape_function
        self.tasks = tasks
        self.data = []

    async def __http_request__async(self, url, session):

        async with session.get(url) as response:
            page_html = await response.read()

            return self.scrape_function(page_html)

    async def __async_scraper(self):

        tasks = []
        async with aiohttp.ClientSession() as session:
            for n in self.tasks:
                tasks.append(self.__http_request__async(n, session))

            self.data = await asyncio.gather(*tasks)

    def run_connector(self):

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__async_scraper())

        return self.data
