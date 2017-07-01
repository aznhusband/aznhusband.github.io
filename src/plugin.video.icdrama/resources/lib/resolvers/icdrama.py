import re
import urlresolver
from bs4 import BeautifulSoup
from resources.lib import common
from urlresolver.resolver import UrlResolver, ResolverError

class Icdrama(UrlResolver):
    name = 'Icdrama'
    host = 'icdrama.se'
    domains = [host]

    def get_media_url(self, host, media_id):
        weburl = self.get_url(host, media_id)

        html = common.webread(weburl)
        if not html:
            common.error("Icdrama resolver: Couldn't get html from " + weburl)
            return ''

        soup = BeautifulSoup(html, 'html5lib')
        if not soup:
            common.error("Icdrama resolver: Couldn't parse html from " + weburl)
            return ''

        iframe = soup.find('iframe')
        if not iframe:
            common.error("Icdrama resolver: Couldn't iframe in html from " + weburl)
            return ''

        url = iframe['src']
        if not url:
            common.error("Icdrama resolver: Couldn't find url in html from " + weburl)
            return ''

        mediaurl = urlresolver.resolve(url)
        if not mediaurl:
            common.error("Icdrama resolver: resolve failed for mediaurl " + url)
            return ''

        return mediaurl

    def get_url(self, host, media_id):
        if host != self.host:
            raise ResolverError('Icdrama resolver: Invalid host: ' + host)
        return 'http://%s/%s.html' % (host, media_id)

    url_pattern = re.compile(r'http://(%s)/([^\.]+)\.html' % re.escape(host))
    def get_host_and_id(self, url):
        r = re.match(self.url_pattern, url)
        try:
            return r.groups()
        except AttributeError:
            raise ResolverError('Icdrama resolver: Invalid URL: ' + url)

    def valid_url(self, web_url, host):
        r = re.match(self.url_pattern, web_url)
        return bool(r) or (host == self.host)

    @classmethod
    def _is_enabled(cls):
        return True
