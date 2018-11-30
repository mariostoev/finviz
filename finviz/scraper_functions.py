from lxml import etree
import os


def get_total_rows(page_content):

    """
    Gets the total rows of the table. This function is called when the user does not provide a number of rows that have to be scraped.
    """

    total_element = page_content.cssselect('td[width="140"]')

    return int(etree.tostring(total_element[0]).decode("utf-8").split('</b>')[1].split(' ')[0])


def get_page_urls(page_content, rows, url):

    """ Gets the page URL addresses """

    try:
        total_pages = int([i.text.split('/')[1] for i in page_content.cssselect('option[value="1"]')][0])
    except IndexError:
        raise Exception("No results matching the criteria: {}"
                        .format(url.split('?', 1)[1]))

    urls = []

    for page_number in range(1, total_pages + 1):

        sequence = 1 + (page_number - 1) * 20

        if sequence - 20 <= rows < sequence:
            break
        else:
            urls.append(url + '&r={}'.format(str(sequence)))

    return urls


def download_image(page_content, url):

    file_name = url.split('t=')[1] + '.jpg'

    if not os.path.exists('charts'):
        os.mkdir('charts')

    with open('charts/' + file_name, 'wb') as handle:
        handle.write(page_content)
