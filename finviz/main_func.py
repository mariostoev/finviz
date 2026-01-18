from datetime import datetime

from lxml import etree

from finviz.helper_functions.request_functions import http_request_get
from finviz.helper_functions.scraper_functions import get_table

STOCK_URL = "https://finviz.com/quote.ashx"
NEWS_URL = "https://finviz.com/news.ashx"
CRYPTO_URL = "https://finviz.com/crypto_performance.ashx"
STOCK_PAGE = {}


def get_page(ticker, force_refresh=False):
    """
    Fetches and caches the stock page for a given ticker.

    :param ticker: stock symbol
    :type ticker: str
    :param force_refresh: force re-fetching the page
    :type force_refresh: bool
    """
    global STOCK_PAGE

    if force_refresh or ticker not in STOCK_PAGE:
        STOCK_PAGE[ticker], _ = http_request_get(
            url=STOCK_URL, payload={"t": ticker}, parse=True
        )


def get_stock(ticker):
    """
    Returns a dictionary containing stock data.

    :param ticker: stock symbol
    :type ticker: str
    :return dict
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]

    data = {}

    # Extract basic info from the new header structure
    # Ticker
    ticker_elem = page_parsed.cssselect('h1.quote-header_ticker-wrapper_ticker')
    if ticker_elem:
        data["Ticker"] = ticker_elem[0].text_content().strip()
    else:
        data["Ticker"] = ticker

    # Company name and website
    company_elem = page_parsed.cssselect('h2.quote-header_ticker-wrapper_company a.tab-link')
    if company_elem:
        data["Company"] = company_elem[0].text_content().strip()
        company_link = company_elem[0].attrib.get("href", "")
        data["Website"] = company_link if company_link.startswith("http") else None
    else:
        data["Company"] = ""
        data["Website"] = None

    # Sector, Industry, Country from the quote-links section
    quote_links = page_parsed.cssselect('div.quote-links a.tab-link')
    sector_industry_country = []
    for link in quote_links:
        href = link.attrib.get("href", "")
        # Links to screener with sector/industry/country filters
        if "f=sec_" in href or "f=ind_" in href or "f=geo_" in href:
            sector_industry_country.append(link.text_content().strip())

    if len(sector_industry_country) >= 3:
        data["Sector"] = sector_industry_country[0]
        data["Industry"] = sector_industry_country[1]
        data["Country"] = sector_industry_country[2]
    elif len(sector_industry_country) == 2:
        data["Sector"] = sector_industry_country[0]
        data["Industry"] = sector_industry_country[1]
        data["Country"] = ""
    elif len(sector_industry_country) == 1:
        data["Sector"] = sector_industry_country[0]
        data["Industry"] = ""
        data["Country"] = ""

    # Extract financial data from the snapshot table
    # The table uses tr.table-dark-row with td.snapshot-td2 cells
    all_rows = page_parsed.cssselect('tr.table-dark-row')

    for row in all_rows:
        cells = row.cssselect('td.snapshot-td2')
        # Cells come in pairs: label, value, label, value, ...
        for i in range(0, len(cells) - 1, 2):
            label_cell = cells[i]
            value_cell = cells[i + 1]

            # Get label text (may contain links)
            label = label_cell.text_content().strip()
            # Get value text (usually in <b> tag)
            value = value_cell.text_content().strip()

            if not label:
                continue

            # Handle special cases
            if label == "EPS next Y" and "EPS next Y" in data:
                # Second occurrence is EPS growth next Y
                data["EPS growth next Y"] = value
                continue
            elif label == "Volatility":
                vols = value.split()
                if len(vols) >= 2:
                    data["Volatility (Week)"] = vols[0]
                    data["Volatility (Month)"] = vols[1]
                elif len(vols) == 1:
                    data["Volatility (Week)"] = vols[0]
                    data["Volatility (Month)"] = vols[0]
                continue

            data[label] = value

    return data


def get_insider(ticker):
    """
    Returns a list of dictionaries containing all recent insider transactions.

    :param ticker: stock symbol
    :return: list
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]

    # Try new table structure first (styled-table-new)
    outer_tables = page_parsed.cssselect('table.styled-table-new')

    # Find the insider trading table by checking for the "Insider Trading" header
    insider_table = None
    for table in outer_tables:
        headers = table.cssselect('thead th')
        if headers and any("Insider Trading" in h.text_content() for h in headers):
            insider_table = table
            break

    # Fallback to old class if not found
    if insider_table is None:
        old_tables = page_parsed.cssselect('table.body-table.insider-trading-table')
        if old_tables:
            insider_table = old_tables[0]

    if insider_table is None:
        return []

    # Extract headers
    header_elements = insider_table.cssselect('thead th')
    if header_elements:
        headers = [h.text_content().strip() for h in header_elements]
    else:
        # Fallback for old structure
        first_row = insider_table.cssselect('tr')[0] if insider_table.cssselect('tr') else None
        if first_row is None:
            return []
        headers = [td.text_content().strip() for td in first_row.cssselect('td')]

    # Extract data rows
    data = []
    tbody = insider_table.cssselect('tbody')
    if tbody:
        rows = tbody[0].cssselect('tr')
    else:
        rows = insider_table.cssselect('tr')[1:]  # Skip header row

    for row in rows:
        cells = row.cssselect('td')
        if len(cells) >= len(headers):
            row_data = {}
            for i, header in enumerate(headers):
                row_data[header] = cells[i].text_content().strip()
            data.append(row_data)

    return data


def get_news(ticker):
    """
    Returns a list of tuples containing (timestamp, headline, url, source) for stock news.

    :param ticker: stock symbol
    :return: list of tuples (timestamp, headline, url, source)
    """

    get_page(ticker)
    page_parsed = STOCK_PAGE[ticker]
    news_table = page_parsed.cssselect('table#news-table')

    if len(news_table) == 0:
        return []

    rows = news_table[0].cssselect('tr')

    results = []
    current_date = datetime.now().date()

    for row in rows:
        try:
            cells = row.cssselect('td')
            if len(cells) < 2:
                continue

            # Get timestamp from first cell
            raw_timestamp = cells[0].text_content().strip()

            # Parse timestamp - handles various formats:
            # "Today 12:00PM", "Jan-18-26 12:00PM", "12:00PM"
            parsed_timestamp = None

            if "Today" in raw_timestamp:
                # Format: "Today 12:00PM"
                time_part = raw_timestamp.replace("Today", "").strip()
                try:
                    parsed_time = datetime.strptime(time_part, "%I:%M%p")
                    parsed_timestamp = datetime.combine(datetime.now().date(), parsed_time.time())
                    current_date = parsed_timestamp.date()
                except ValueError:
                    continue
            elif len(raw_timestamp) > 8 and "-" in raw_timestamp:
                # Format: "Jan-18-26 12:00PM" (full date with time)
                try:
                    parsed_timestamp = datetime.strptime(raw_timestamp, "%b-%d-%y %I:%M%p")
                    current_date = parsed_timestamp.date()
                except ValueError:
                    # Try alternative format
                    try:
                        parsed_timestamp = datetime.strptime(raw_timestamp, "%b-%d-%Y %I:%M%p")
                        current_date = parsed_timestamp.date()
                    except ValueError:
                        continue
            else:
                # Format: "12:00PM" (time only, use current_date)
                try:
                    parsed_time = datetime.strptime(raw_timestamp, "%I:%M%p")
                    parsed_timestamp = datetime.combine(current_date, parsed_time.time())
                except ValueError:
                    continue

            if parsed_timestamp is None:
                continue

            # Get headline and URL from news link
            news_link = cells[1].cssselect('a.tab-link-news')
            if not news_link:
                continue

            headline = news_link[0].text_content().strip()
            url = news_link[0].get("href", "")

            # Get source from news-link-right span
            source = ""
            source_elem = cells[1].cssselect('div.news-link-right span')
            if source_elem:
                source_text = source_elem[0].text_content().strip()
                # Remove parentheses: "(MarketWatch)" -> "MarketWatch"
                source = source_text.strip("()")

            results.append((
                parsed_timestamp.strftime("%Y-%m-%d %H:%M"),
                headline,
                url,
                source
            ))
        except (IndexError, AttributeError):
            continue

    return results


def get_all_news():
    """
    Returns a list of sets containing time, headline and url
    :return: list
    """

    page_parsed, _ = http_request_get(url=NEWS_URL, parse=True)
    all_dates = [
        row.text_content() for row in page_parsed.cssselect('td[class="nn-date"]')
    ]
    all_headlines = [
        row.text_content() for row in page_parsed.cssselect('a[class="nn-tab-link"]')
    ]
    all_links = [
        row.get("href") for row in page_parsed.cssselect('a[class="nn-tab-link"]')
    ]

    return list(zip(all_dates, all_headlines, all_links))


def get_crypto(pair):
    """

    :param pair: crypto pair
    :return: dictionary
    """

    page_parsed, _ = http_request_get(url=CRYPTO_URL, parse=True)
    page_html, _ = http_request_get(url=CRYPTO_URL, parse=False)
    crypto_headers = page_parsed.cssselect('tr[valign="middle"]')[0].xpath("td//text()")
    crypto_table_data = get_table(page_html, crypto_headers)

    return crypto_table_data[pair]


def get_analyst_price_targets(ticker, last_ratings=5):
    """
    Returns a list of dictionaries containing all analyst ratings and price targets.

    Each dictionary contains:
    - date: rating date (YYYY-MM-DD format)
    - category: rating category (e.g., "Reiterated", "Upgrade", "Downgrade")
    - analyst: analyst firm name
    - rating: rating action (e.g., "Buy", "Hold", "Sell")
    - target_from: previous price target (if available)
    - target_to: new price target (if available)
    - target: single price target (if only one is provided)

    :param ticker: stock symbol
    :param last_ratings: number of most recent ratings to return
    :return: list of dictionaries
    """

    analyst_price_targets = []

    try:
        get_page(ticker)
        page_parsed = STOCK_PAGE[ticker]

        # Try new table class first
        tables = page_parsed.cssselect('table.js-table-ratings')
        if not tables:
            # Fallback to old class
            tables = page_parsed.cssselect('table.fullview-ratings-outer')

        if not tables:
            return []

        table = tables[0]

        # Get rows from tbody if present, otherwise from table directly
        tbody = table.cssselect('tbody')
        if tbody:
            rows = tbody[0].cssselect('tr')
        else:
            rows = table.cssselect('tr')

        for row in rows:
            try:
                cells = row.cssselect('td')
                if len(cells) < 4:
                    continue

                # Extract text from each cell
                rating_data = [cell.text_content().strip() for cell in cells]
                rating_data = [val.replace("→", "->").replace("$", "") for val in rating_data if val]

                if len(rating_data) < 4:
                    continue

                # Parse date
                try:
                    date_str = datetime.strptime(rating_data[0], "%b-%d-%y").strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        date_str = datetime.strptime(rating_data[0], "%b-%d-%Y").strftime("%Y-%m-%d")
                    except ValueError:
                        continue

                data = {
                    "date": date_str,
                    "category": rating_data[1],
                    "analyst": rating_data[2],
                    "rating": rating_data[3],
                }

                # Handle price targets (5th column if present)
                if len(rating_data) >= 5 and rating_data[4]:
                    price_str = rating_data[4].replace(" ", "")
                    if "->" in price_str:
                        parts = price_str.split("->")
                        if len(parts) == 2:
                            try:
                                data["target_from"] = float(parts[0]) if parts[0] else 0.0
                                data["target_to"] = float(parts[1]) if parts[1] else 0.0
                            except ValueError:
                                pass
                    else:
                        try:
                            data["target"] = float(price_str)
                        except ValueError:
                            pass

                analyst_price_targets.append(data)
            except (IndexError, AttributeError):
                continue

    except Exception:
        pass

    return analyst_price_targets[:last_ratings]
