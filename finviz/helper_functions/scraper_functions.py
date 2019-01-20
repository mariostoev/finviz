from lxml import etree
from lxml import html
import os


def get_table(page_html, headers, rows=None, url=None):
    """ Private function used to return table data inside a list of dictonaries. """

    page_parsed = parse(page_html)
    # When we call this method from Portfolio we don't fill the rows argument.
    # Conversly, we always fill the rows argument when we call this method from Screener.
    # Also, in the portfolio page, we don't need the last row - it's redundant.
    if rows is None:
        rows = -2  # We'll increment it later (-1) and use it to cut the last row

    data_sets = []
    # Select the HTML of the rows and append each column text to a list
    # Skip the first element ([1:]), since it's the headers (we already have it as a constant)
    all_rows = [column.xpath('td//text()') for column in page_parsed.cssselect('tr[valign="top"]')[1:rows + 1]]

    # If rows is different from -2, this function is called from Screener
    if rows != -2:
        for row in all_rows:
            # If we reach the last row that's required by the user
            if int(row[0]) == rows:
                data_sets.append(dict(zip(headers, row)))
                break
            else:
                data_sets.append(dict(zip(headers, row)))
    else:
        # Zip each row values to the headers and append them to data_sets
        [data_sets.append(dict(zip(headers, row))) for row in all_rows]

    return data_sets


def get_total_rows(page_content):
    """ Returns the total number of rows(results). """

    total_element = page_content.cssselect('td[width="140"]')
    total_number = etree.tostring(total_element[0]).decode('utf-8').split('</b>')[1].split()[0]

    try:
        return int(total_number)
    except ValueError:
        return 0


def get_page_urls(page_content, rows, url):
    """ Returns a list containing all of the page URL addresses. """

    total_pages = int([i.text.split('/')[1] for i in page_content.cssselect('option[value="1"]')][0])
    urls = []

    for page_number in range(1, total_pages + 1):

        sequence = 1 + (page_number - 1) * 20

        if sequence - 20 <= rows < sequence:
            break
        else:
            urls.append(url + f'&r={str(sequence)}')

    return urls


def download_chart_image(page_content, url):
    """ Downloads a .jpg image of a chart into the "charts" folder. """

    file_name = url.split('t=')[1] + '.jpg'

    if not os.path.exists('charts'):
        os.mkdir('charts')

    with open('charts/' + file_name, 'wb') as handle:
        handle.write(page_content)


def parse(page):
    """ Parses the HTML contents of a page. """
    return html.fromstring(page)
