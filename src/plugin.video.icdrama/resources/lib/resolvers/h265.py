import re
import urllib
import urlresolver
import xbmcaddon
from resources.lib import common
from urlresolver.resolver import UrlResolver, ResolverError
from urlresolver.plugins.lib import jsunpack

class H265(UrlResolver):
    name = 'H265'
    host = 'h265.se'
    domains = [host]

    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)

        html = common.webread(url)
        if not len(html):
            raise ResolverError('H265 resolver: no html from ' + url)

        streams = self._extract_streams(html)

        if not streams:
            raise ResolverError('H265 resolver: no streams found in ' + url)

        urls, labels = zip(*streams)

        if len(labels) == 1:
            ind = 0
        else:
            heading = xbmcaddon.Addon().getLocalizedString(33100)
            ind = common.select(heading, labels)
            if ind < 0:
                common.error("H265 resolver: stream selection cancelled")
                return ''

        return urls[ind] + '|User-Agent=' + urllib.quote(xbmcaddon.Addon().getSetting('user_agent'))

    def get_url(self, host, media_id):
        if host != self.host:
            raise ResolverError('H265 resolver: Invalid host: %s' % host)
        return 'http://%s/%s' % (host, media_id)

    url_pattern = re.compile(r'http://(%s)/(.*)' % re.escape(host))
    def get_host_and_id(self, url):
        r = re.match(self.url_pattern, url)
        try:
            return r.groups()
        except AttributeError:
            raise ResolverError('H265 resolver: Invalid URL: %s' % url)

    def valid_url(self, web_url, host):
        r = re.match(self.url_pattern, web_url)
        return bool(r) or (host == self.host)

    def _extract_streams(self, html):
        '''Return list of streams (tuples (url, label))
        '''
        streams = [] # list of tuples (url, label)

        if jsunpack.detect(html):
            urls = re.findall(r'file:\"(.+?)\"', jsunpack.unpack(html))
            for url in urls:
                if ".jpg" in url:
                    urls.remove(url)
            labels = []
            for i in range(len(urls)):
                labels.append('Stream ' + str(i + 1))
            streams = zip(urls, labels)

        return streams

    @classmethod
    def _is_enabled(cls):
        return True
