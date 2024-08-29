import requests
from bs4 import BeautifulSoup


def get_status_code(url):
    r = requests.get(url)
    status = r.status_code
    return status


def get_raise_for_status(url):
    r = requests.get(url)
    return r.raise_for_status()


def parser_url(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = ''
    for meta in soup.find_all('meta'):
        if meta.get('name') == 'description':
            description = meta.get('content')
    return {'h1': h1, 'title': title, 'description': description}
