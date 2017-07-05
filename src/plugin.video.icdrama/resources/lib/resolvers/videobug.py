import re
import json
import urllib
import base64
import urlresolver
import xbmcaddon
from bs4 import BeautifulSoup
from resources.lib import common
from urlresolver.resolver import UrlResolver, ResolverError
from urlresolver.plugins.lib import jsunpack

class Videobug(UrlResolver):
    name = 'Videobug'
    host = 'videobug.se'
    domains = [host]

    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)

        html = common.webread(url)
        if not len(html):
            raise ResolverError('Videobug resolver: no html from ' + url)

        streams = self._extract_streams(html)

        if not streams:
            raise ResolverError('Videobug resolver: no streams found in ' + url)

        urls, labels = zip(*streams)

        if len(labels) == 1:
            ind = 0
        else:
            heading = xbmcaddon.Addon().getLocalizedString(33100)
            ind = common.select(heading, labels)
            if ind < 0:
                common.error("Videobug resolver: stream selection cancelled")
                return ''

        if ('redirector.googlevideo.com' in urls[ind] or
            'blogspot.com' in urls[ind]):
            # Kodi can play directly, skip further resolve
            return urls[ind]
        else:
            mediaurl = urlresolver.resolve(urls[ind])
            if not mediaurl:
                raise ResolverError("Videobug resolver: resolve failed for mediaurl " + urls[ind])

            return mediaurl

    def get_url(self, host, media_id):
        if host != self.host:
            raise ResolverError('Videobug resolver: Invalid host: %s' % host)
        return 'http://%s/%s' % (host, media_id)

    url_pattern = re.compile(r'http://(%s)/(.*)' % re.escape(host))
    def get_host_and_id(self, url):
        r = re.match(self.url_pattern, url)
        try:
            return r.groups()
        except AttributeError:
            raise ResolverError('Videobug resolver: Invalid URL: %s' % url)

    def valid_url(self, web_url, host):
        r = re.match(self.url_pattern, web_url)
        return bool(r) or (host == self.host)

    def _unobscurify(self, s, key):
        return urllib.unquote(''.join(chr(ord(c) - key) for c in urllib.unquote(s)))

    def _extract_streams(self, html):
        '''Return list of streams (tuples (url, label))
        '''
        streams = [] # list of tuples (url, label)

        df = re.search(r"dF\(\\?'(.*)\\?'\)", html)
        if df:
            script_end = html.find('</script>', df.end())
            script_end = script_end + 9 if script_end > -1 else -1
            unobscured = ''
            result = False
            for key in range(1, 255):
                unobscured = self._unobscurify(df.group(1), key)
                result = bool(BeautifulSoup(unobscured, "html5lib").find('script'))
                if result:
                    break

            if not result:
                raise ResolverError('Videobug resolver: error unobscurifying dF()')

            html = html[:script_end] + unobscured + html[script_end:]
        else:
            raise ResolverError('Videobug resolver: no dF() found')

        # Allupload
        # http://videobug.se/vid-a/g2S5k34-MoC2293iUaa9Hw
        json_data = re.findall(r"json_data = '(.+)';", html)
        if json_data:
            strdecode_1 = lambda s: base64.b64decode(urllib.unquote(s)[::-1]) # no longer used?
            strdecode_2 = lambda s: base64.b64decode(urllib.unquote(s))
            try:
                hashes = json.loads(json_data[0])
                exclude = ['Subtitles', 'image', 'JS', 'ADV']
                videos = [h for h in hashes if h['s'] not in exclude]
                # try both decode methods
                try:
                    streams = [(strdecode_1(h['u']), h['s']) for h in videos]
                except Exception:
                    streams = [(strdecode_2(h['u']), h['s']) for h in videos]
            except Exception:
                pass

        # Picasaweb, Videobug
        # http://videobug.se/video/Wz3_oCoEYozRSbJFQo4fkjmuvR6LpsFHM-XZya5tuk6stTXWdUeyplq5vVvSm0Yr0MXPFUmLt2XqrbLMPnE_Mgz8NbhXMZ6XFDI4hj253Z7af95WQPPDlpizIuuUXavEJqB8-bXuKbx6HTCMb5p5FC90yg1kXJb6?
        if not streams:
            soup = BeautifulSoup(html, 'html5lib')
            player_func = re.compile(r'(player_[^\(]+)\(\);').match
            butts = soup.find_all('input', type='button', onclick=player_func)

            funcs = [player_func(b['onclick']).group(1) for b in butts]
            labels = [b['value'] for b in butts]

            try:
                func_bodies = [re.findall(r'%s\(\) *{(.+)};' % f, html)[0] for f in funcs]
                re_flash = re.compile(r"video *= *{[^:]+: *'(.*?)' *}")
                re_html5 = re.compile(r'<source.*?src=\"(.*?)\"')

                urls = [(re_flash.findall(fb) or re_html5.findall(fb))[0] for fb in func_bodies]
                streams = zip(urls, labels)
            except Exception:
                pass

        # http://videobug.se/vid-al/XNkjCT5pBx1YlndruYWdWg?&caption=-sgCv7BkuLZn41-ZxxJZhTsKYcZIDgJPGYNOuIpulC_4kcrZ9k3fGQabH5rDAKgiLMVJdesVZPs
        if not streams:
            vids = re.findall(r'''{ *file *: *strdecode\('(.+?)'\).*?label *: *"(.*?)"''', html)
            for cryptic_url, label in vids:
                url = base64.b64decode(urllib.unquote(cryptic_url)[::-1])
                streams.append((url, label))

        # http://videobug.se/vid/pVobcNozEWmTkarNnwX06w
        if not streams:
            if jsunpack.detect(html):
                streams = self._extract_streams(jsunpack.unpack(html))

        # remove this hardcoded youtube link
        streams = [(u, l) for u, l in streams if u != 'https://www.youtube.com/watch?v=niBTIQIYlv8']

        return streams

    @classmethod
    def _is_enabled(cls):
        return True
