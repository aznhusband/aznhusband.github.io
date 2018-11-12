from bs4 import BeautifulSoup
import urlresolver
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class Icdrama(UrlResolver):
    name = 'Icdrama'
    domains = [ 'icdrama.se', 'icdrama.to' ]
    pattern = '(?://|\.)(icdrama\.se|icdrama\.to)/(.+)'


    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):
        try:
            weburl = self.get_url(host, media_id)
            html   = self.net.http_GET(weburl, headers=self.headers).content
            iframe = BeautifulSoup(html, 'html5lib').find('iframe')
            return urlresolver.resolve(iframe['src'])
        except:
            return None


    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'http://{host}/{media_id}')


    @classmethod
    def _is_enabled(cls):
        return True
