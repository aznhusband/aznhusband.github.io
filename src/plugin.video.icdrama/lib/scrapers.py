import re
import urllib.request, urllib.parse, urllib.error
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from lib import cache, config, common

@cache.memoize()
def _get(url):
    # only scrape within the site
    if any(domain in url for domain in config.domains): # good enough check
        # should not be larger than 1MB
        return common.webread(url)
    else:
        raise Exception('Bad URL: %s' % url)

@cache.memoize()
def _soup(url):
    soup = BeautifulSoup(_get(url), 'html5lib')
    return soup

@cache.memoize(10)
def shows(url):
    soup = _soup(url)
    tiles = soup.select('a.movie-image')
    show_list = []
    for t in tiles:
        eng_title = t.select('.movie-overlay-title')[-1].getText()
        all_title = t['title']
        ori_title = all_title.replace(eng_title, '').strip(' -')
        show_url = urljoin(url, t['href'])
        image = re.search(r'url\((.+?)\)', t['style']).group(1)
        show_list.append((eng_title, ori_title, show_url, image))
    return show_list

def search(url):
    # same template as shows
    return shows(url)

@cache.memoize(10)
def pages(url):
    soup = _soup(url)
    pages = soup.select('ul.pager > li > span > a')
    return [(p['title'], urljoin(url, p['href'])) for p in pages]

@cache.memoize(10)
def recent_updates(url):
    soup = _soup(url)
    updates = soup.select('ul.listep > li > a')
    return [(u.getText(), urljoin(url, u['href'])) for u in updates]

@cache.memoize(10)
def versions(url):
    soup = _soup(url)
    butts = [b for b in soup.select('a.btnWatch') if b.getText() != 'Download']
    return [(b.getText(), b['href']) for b in butts]

@cache.memoize(10)
def episodes(url):
    soup = _soup(url)
    epis = soup.find_all('a', 'btn-episode', id=True)
    return [(e.getText(), urljoin(url, e['href'])) for e in epis]

@cache.memoize(10)
def mirrors(url):
    soup = _soup(url)
    mirrs = [node.getText() for node in soup.select('span.tite')]
    mirr_parts = [node.find_all('a', recursive=False)
                  for node in soup.select('ul.tn-uldef')]
    mirr_list = []
    for mirr, parts in zip(mirrs, mirr_parts):
        parts = [(p.getText(), p['href']) for p in parts]
        mirr_list.append((mirr, parts))
    return mirr_list

@cache.memoize(60)
def title_image(mirror_url):
    soup = _soup(mirror_url)
    title = soup.find('meta', {'property': 'title'})['content']
    image = soup.find('meta', {'property': 'og:image'})['content']
    return (title, image)

def category_page(url):
    # Note: use the url itself to get category name and page
    relpath = urlparse(url).path.lstrip('/')
    m = re.search(r'^[A-Za-z-]+', relpath)
    category = m.group(0).replace('-', ' ').capitalize() if m else 'Unknown'
    m = re.search(r'page-(\d+)\.html', relpath)
    page = m.group(1) if m else '1'
    return (category, page)

def search_page(url):
    # Note: use the url itself to get search text and page
    relpath = urlparse(url).path.lstrip('/')
    m = re.search(r'search/([%1-9A-Za-z_\.-]+)', relpath)
    text = urllib.parse.unquote(m.group(1)) if m else ''
    m = re.search(r'page-(\d+)\.html', relpath)
    page = m.group(1) if m else '1'
    return (text, page)

def show_name(url):
    # same template as title_image
    title, _ = title_image(url)
    return title

def version_name(url):
    # same template as title_image
    title, _ = title_image(url)
    return title
