import re
import json
from urllib import unquote
import base64
import requests
from bs4 import BeautifulSoup
import urlresolver
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError
from urlresolver.plugins.lib import jsunpack, helpers

class Videobug(UrlResolver):
    name = 'Videobug'
    domains = [ 'videobug.se' ]
    pattern = '(?://|\.)(videobug\.se)/(.+)'


    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)
        headers = self.headers
        headers['Referer'] = 'http://icdrama.se'

        response = requests.get(url, headers=headers)
        streams = self._extract_streams(response)
        url = helpers.pick_source(streams, auto_pick=False)

        if ('redirector.googlevideo.com' in url or
            'blogspot.com' in url):
            # Kodi can play directly, skip further resolve
            return url

        return urlresolver.resolve(url)


    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'http://{host}/{media_id}')


    def _unobscurify(self, s, term):
        for key in range(1, 255):
            try:
                html = unquote(''.join(chr(ord(c) - key) for c in unquote(s)))
            except:
                html = ''
            if term in html:
                return html
        return ''


    def _extract_streams(self, response):
        '''Return list of streams (tuples (url, label))
        '''
        streams = [] # list of tuples (url, label)

        methods = [ self.__method1, self.__method2, self.__method3, self.__method4, self.__method5 ]
        for method in methods:
            streams = method(response)
            if streams:
                return streams
        raise ResolverError('Videobug resolver: no streams found in ' + url)


    def __method1(self, response):
        streams = []
        # Grab the HTML
        if response.status_code == 200:
            html = response.content
            url  = response.url
        else:
            # error, bail.
            return streams

        # Search for the obscured list of data, and decode.
        oblist = re.search(r"\[([\\\'xa-f0-9,]*)\]", html)
        data = eval(oblist.group(0))
        unobscured = None
        for d in data:
            if len(d) > 10:
                unobscured = self._unobscurify(d, 'V_TOKEN')
                if unobscured:
                    break

        if not unobscured:
            # Might be in the dF
            df = re.search(r"dF\(('[\\xa-f0-9]*')\)", html)
            obscured = eval(df.group(1))
            unobscured = self._unobscurify(obscured, 'V_TOKEN')

        if not unobscured:
            return streams

        # We've found the obscured variables.  Parse them out.
        for var in unobscured.split(';'):
            if 'V_REQUEST' in var:
                V_REQUEST = re.findall(r'\"(.+?)\"', var)[0]
            if 'V_TOKEN' in var:
                V_TOKEN = re.findall(r'\"(.+?)\"', var)[0]
            if 'V_TIME' in var:
                V_TIME = re.findall(r' ([0-9]+)', unobscured)[0]

        # Make the ajax call
        session = requests.Session()
        data = {
                'V_REQUEST': V_REQUEST,
                'V_TOKEN'  : V_TOKEN,
                'V_TIME'   : V_TIME
                }

        self.headers['Referer']          = url
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.headers['Accept']           = 'application/json, text/javascript, */*; q=0.01'
        self.headers['Content-Type']     = 'application/x-www-form-urlencoded; charset=UTF-8'

        response = session.post(url, data = data, headers = self.headers)
        if response.status_code != 200:
            return streams

        hashes = json.loads(response.content)
        if hashes:
            strdecode = lambda s: base64.b64decode(unquote(s))
            exclude = ['Subtitles', 'image', 'JS', 'ADV']
            videos = [h for h in hashes if h['s'] not in exclude]
            streams = [(h['s'], strdecode(h['u'])) for h in videos]

        return streams


    def __method2(self, response):
        ''' Allupload
            http://videobug.se/vid-a/g2S5k34-MoC2293iUaa9Hw
        '''
        html = response.content
        streams = []
        df = re.search(r"dF\(\\?'(.*)\\?'\)", html)
        if df:
            script_end = html.find('</script>', df.end())
            script_end = script_end + 9 if script_end > -1 else -1
            unobscured = self._unobscurify(df.group(1), '<script>')
            html = html[:script_end] + unobscured + html[script_end:]
        json_data = re.findall(r"json_data = '(.+)';", html)
        if json_data:
            strdecode_1 = lambda s: base64.b64decode(unquote(s)[::-1]) # not used?
            strdecode_2 = lambda s: base64.b64decode(unquote(s))
            try:
                hashes = json.loads(json_data[0])
                exclude = ['Subtitles', 'image', 'JS', 'ADV']
                videos = [h for h in hashes if h['s'] not in exclude]
                # try both decode methods
                try:
                    streams = [(h['s'], strdecode_1(h['u'])) for h in videos]
                except Exception:
                    streams = [(h['s'], strdecode_2(h['u'])) for h in videos]
            except Exception:
                pass
        return streams


    def __method3(self, response):
        ''' Picasaweb, Videobug
            http://videobug.se/video/Wz3_oCoEYozRSbJFQo4fkjmuvR6LpsFHM-XZy...
        '''
        html = response.content
        streams = []
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
            streams = zip(labels, urls)
        except Exception:
            pass
        return streams


    def __method4(self, response):
        ''' http://videobug.se/vid-al/XNkjCT5pBx1YlndruYWdWg?&caption=-sgCv7...
        '''
        html = response.content
        streams = []
        vids = re.findall(r'''{ *file *: *strdecode\('(.+?)'\).*?label *: *"(.*?)"''', html)
        for cryptic_url, label in vids:
            url = base64.b64decode(unquote(cryptic_url)[::-1])
            streams.append((label, url))
        return streams


    def __method5(self, response):
        ''' http://videobug.se/vid/pVobcNozEWmTkarNnwX06w
        '''
        html = response.content
        streams = []
        if jsunpack.detect(html):
            streams = self._extract_streams(jsunpack.unpack(html))
        return streams


    @classmethod
    def _is_enabled(cls):
        return True
