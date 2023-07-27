import datetime
import os
import time

import requests
from lxml import etree, html


def get_table(page_html: requests.Response, headers, rows=None, **kwargs):
    """ Private function used to return table data inside a list of dictionaries. """
    if isinstance(page_html, str):
        page_parsed = html.fromstring(page_html)
    else:
        page_parsed = html.fromstring(page_html.text)
    # When we call this method from Portfolio we don't fill the rows argument.
    # Conversely, we always fill the rows argument when we call this method from Screener.
    # Also, in the portfolio page, we don't need the last row - it's redundant.
    if rows is None:
        rows = -2  # We'll increment it later (-1) and use it to cut the last row

    data_sets = []
    # Select the HTML of the rows and append each column text to a list
    all_rows = [
        column.xpath("td//text()")
        for column in page_parsed.cssselect('tr[valign="top"]')
    ]

    # If rows is different from -2, this function is called from Screener
    if rows != -2:
        for row_number, row_data in enumerate(all_rows, 1):
            data_sets.append(dict(zip(headers, row_data)))
            if row_number == rows:  # If we have reached the required end
                break
    else:
        # Zip each row values to the headers and append them to data_sets
        [data_sets.append(dict(zip(headers, row))) for row in all_rows]

    return data_sets


def get_total_rows(page_content):
    """ Returns the total number of rows(results). """
    total_number = str(html.tostring(page_content)).split('class="count-text">#1 / ')[1].split(' Total</td>')[0]
    try:
        return int(total_number)
    except ValueError:
        return 0


def get_page_urls(page_content, rows, url):
    """ Returns a list containing all of the page URL addresses. """

    total_pages = int(
        [i.text.split("/")[1] for i in page_content.cssselect('option[value="1"]')][0]
    )
    urls = []

    for page_number in range(1, total_pages + 1):
        sequence = 1 + (page_number - 1) * 20

        if sequence - 20 <= rows < sequence:
            break
        urls.append(url + f"&r={str(sequence)}")

    return urls


def download_chart_image(page_content: requests.Response, **kwargs):
    """ Downloads a .png image of a chart into the "charts" folder. """
    file_name = f"{kwargs['URL'].split('t=')[1]}_{int(time.time())}.png"

    if not os.path.exists("charts"):
        os.mkdir("charts")

    with open(os.path.join("charts", file_name), "wb") as handle:
        handle.write(page_content.content)


def get_analyst_price_targets_for_export(
    ticker=None, page_content=None, last_ratings=5
):
    analyst_price_targets = []

    try:
        table = page_content.cssselect('table[class="fullview-ratings-outer"]')[0]
        ratings_list = [row.xpath("td//text()") for row in table]
        ratings_list = [
            [val for val in row if val != "\n"] for row in ratings_list
        ]  # remove new line entries

        headers = [
            "ticker",
            "date",
            "category",
            "analyst",
            "rating",
            "price_from",
            "price_to",
        ]  # header names
        count = 0

        for row in ratings_list:
            if count == last_ratings:
                break

            price_from, price_to = (
                0,
                0,
            )  # default values for len(row) == 4 , that is there is NO price information
            if len(row) == 5:
                strings = row[4].split("→")
                if len(strings) == 1:
                    price_to = (
                        strings[0].strip(" ").strip("$")
                    )  # if only ONE price is available then it is 'price_to' value
                else:
                    price_from = (
                        strings[0].strip(" ").strip("$")
                    )  # both '_from' & '_to' prices available
                    price_to = strings[1].strip(" ").strip("$")

            elements = [
                ticker,
                datetime.datetime.strptime(row[0], "%b-%d-%y").strftime("%Y-%m-%d"),
            ]
            elements.extend(row[1:3])
            elements.append(row[3].replace("→", "->"))
            elements.append(price_from)
            elements.append(price_to)
            data = dict(zip(headers, elements))
            analyst_price_targets.append(data)
            count += 1
    except Exception:
        pass

    return analyst_price_targets


def download_ticker_details(page_content: requests.Response, **kwargs):
    data = {}
    ticker = kwargs["URL"].split("=")[1]
    page_parsed = html.fromstring(page_content.text)

    all_rows = [
        row.xpath("td//text()")
        for row in page_parsed.cssselect('tr[class="table-dark-row"]')
    ]

    for row in all_rows:
        for column in range(0, 11):
            if column % 2 == 0:
                data[row[column]] = row[column + 1]

    if len(data) == 0:
        print(f"-> Unable to parse page for ticker: {ticker}")

    return {ticker: [data, get_analyst_price_targets_for_export(ticker, page_parsed)]}
