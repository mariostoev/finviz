from lxml import etree


def get_total_rows(page_content):
    total_element = page_content.cssselect('td[width="140"]')

    return int(etree.tostring(total_element[0]).decode("utf-8").split('</b>')[1].split(' ')[0])


def get_page_urls(page_content, rows, url):

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
