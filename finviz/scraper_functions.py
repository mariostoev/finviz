from lxml import etree
import os


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


def download_chart_image(page_content, url):
    """ Downloads a .jpg image of a chart into the "charts" folder. """

    file_name = url.split('t=')[1] + '.jpg'

    if not os.path.exists('charts'):
        os.mkdir('charts')

    with open('charts/' + file_name, 'wb') as handle:
        handle.write(page_content)
