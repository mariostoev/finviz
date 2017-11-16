from urllib.request import urlopen
from bs4 import BeautifulSoup
from lxml import html
import urllib
import requests
import json

class Finviz():


    def __init__ (self):
        self.screener_url = 'https://finviz.com/screener.ashx'
        self.main_url = 'https://finviz.com'
        self.user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
        self.save_format = 'JSON'

    def scrape_content(self, url, quantity):
        htmlPage = urllib.request.Request(url)
        scrapePage = urlopen(htmlPage).read()
        pageContent = BeautifulSoup(scrapePage, 'html.parser')

        data = {

        }

        with open('data.json', 'w') as output:
            for tbody in pageContent('table', {'bgcolor': '#d3d3d3'}):
                for eachRow in tbody.findAll('tr')[1:]:
                    info = eachRow.findAll('a')

                    rowData = {
                        info[0].text : {
                            'Number': info[0].text,
                            'Ticker': info[1].text,
                            'Company': info[2].text,
                            'Sector': info[3].text,
                            'Industry': info[4].text,
                            'Country': info[5].text,
                            'Market Cap': info[6].text,
                            'P/E': info[7].text,
                            'Price': info[8].text,
                            'Change': info[9].text,
                            'Volume': info[10].text
                        }
                    }

                    data.update(rowData)

                json.dump(data, output, indent=4)


        return 0  # Finished in 4.5s


    def url_query(self, payload, quantity):
        if payload is None:
            payload = []

        payload['user-agent'] = self.user_agent
        r = requests.get(self.screener_url, params=payload)

        print(r.url)
        return self.scrape_content(r.url, quantity)

    def search(self, tickers=None, filters=None, sort_by=None, quantity=50):
        if tickers is None:
            tickers = []

        if filters is None:
            filters = []

        if sort_by is None:
            sort_by = ''

        payload = {
            'v': '111',  # Overview search
            't': ','.join(tickers),
            'f': ','.join(filters),
            'o': sort_by
        }

        return self.url_query(payload, quantity)
