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

    options=[('class="count-text whitespace-nowrap">#1 / ',' Total</div>'),('class="count-text">#1 / ',' Total</td>')]
    page_text = str(html.tostring(page_content))
    for option_beg,option_end in options:
        if option_beg in page_text:
            total_number = page_text.split(option_beg)[1].split(option_end)[0]
            try:
                return int(total_number)
            except ValueError:
                return 0
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
    """
    Extract analyst price targets from a stock page for CSV export.

    :param ticker: stock symbol
    :param page_content: parsed HTML content
    :param last_ratings: number of ratings to return
    :return: list of dictionaries
    """
    analyst_price_targets = []

    try:
        # Try new table class first
        tables = page_content.cssselect('table.js-table-ratings')
        if not tables:
            # Fallback to old class
            tables = page_content.cssselect('table.fullview-ratings-outer')

        if not tables:
            return analyst_price_targets

        table = tables[0]

        # Get rows from tbody if present
        tbody = table.cssselect('tbody')
        if tbody:
            rows = tbody[0].cssselect('tr')
        else:
            rows = table.cssselect('tr')

        headers = [
            "ticker",
            "date",
            "category",
            "analyst",
            "rating",
            "price_from",
            "price_to",
        ]
        count = 0

        for row_elem in rows:
            if count == last_ratings:
                break

            cells = row_elem.cssselect('td')
            if len(cells) < 4:
                continue

            row = [cell.text_content().strip() for cell in cells]
            row = [val for val in row if val]  # Remove empty values

            if len(row) < 4:
                continue

            price_from, price_to = 0, 0

            if len(row) >= 5 and row[4]:
                price_str = row[4].replace("$", "")
                strings = price_str.split("→") if "→" in price_str else price_str.split("->")
                if len(strings) == 1:
                    price_to = strings[0].strip()
                elif len(strings) == 2:
                    price_from = strings[0].strip()
                    price_to = strings[1].strip()

            try:
                date_str = datetime.datetime.strptime(row[0], "%b-%d-%y").strftime("%Y-%m-%d")
            except ValueError:
                try:
                    date_str = datetime.datetime.strptime(row[0], "%b-%d-%Y").strftime("%Y-%m-%d")
                except ValueError:
                    continue

            elements = [
                ticker,
                date_str,
                row[1],
                row[2],
                row[3].replace("→", "->"),
                price_from,
                price_to,
            ]
            data = dict(zip(headers, elements))
            analyst_price_targets.append(data)
            count += 1
    except Exception:
        pass

    return analyst_price_targets


def download_ticker_details(page_content: requests.Response, **kwargs):
    """
    Download and parse ticker details from a stock page.

    :param page_content: HTTP response containing the page
    :return: dictionary with ticker data and analyst price targets
    """
    data = {}
    ticker = kwargs["URL"].split("=")[1]
    page_parsed = html.fromstring(page_content.text)

    # Use the new table structure with snapshot-td2 cells
    all_rows = page_parsed.cssselect('tr.table-dark-row')

    for row in all_rows:
        cells = row.cssselect('td.snapshot-td2')
        # Cells come in pairs: label, value, label, value, ...
        for i in range(0, len(cells) - 1, 2):
            label = cells[i].text_content().strip()
            value = cells[i + 1].text_content().strip()
            if label:
                data[label] = value

    # Fallback to old xpath method if new method returns empty
    if len(data) == 0:
        all_rows_old = [
            row.xpath("td//text()")
            for row in page_parsed.cssselect('tr.table-dark-row')
        ]
        for row in all_rows_old:
            for column in range(0, min(11, len(row) - 1)):
                if column % 2 == 0:
                    data[row[column]] = row[column + 1]

    if len(data) == 0:
        print(f"-> Unable to parse page for ticker: {ticker}")

    return {ticker: [data, get_analyst_price_targets_for_export(ticker, page_parsed)]}
