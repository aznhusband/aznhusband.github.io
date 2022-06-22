import re
import json
from urllib.parse import unquote
from urllib.parse import urlparse
import base64
import requests
from bs4 import BeautifulSoup
import resolveurl
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl.lib import jsunpack, helpers
from .. import common as cmn

class Videobug(ResolveUrl):
    name = 'Videobug'
    domains = [ 'videobug.se', 'vlist.se']
    pattern = '(?://|\.)(videobug\.se|vlist\.se)/(.+)'

    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)
        headers = self.headers
        headers['Referer'] = 'http://icdrama.se'

        response = requests.get(url, headers=headers)

        unwrapped_url = ''
        if 'videoredirect.php?' in url: #for current Openload source & other possible redirects
            unwrapped_url = response.url
        else:
            streams = self._extract_streams(response)
            unwrapped_url = helpers.pick_source(streams, auto_pick=False)

        unwrapped_url = unwrapped_url.decode("utf-8")
        if ('redirector.googlevideo.com' in unwrapped_url or
            'blogspot.com' in unwrapped_url or
            'fbcdn.net' in unwrapped_url): #for current Videobug source
            # Kodi can play directly, skip further resolve
            return unwrapped_url

        return resolveurl.resolve(unwrapped_url)


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

        methods = [self.__method6]
        for method in methods:
            streams = method(response)
            if streams:
                return streams
        raise ResolverError('Videobug resolver: no streams found in ' + response.url)

    def __method6(self, response):
        streams = []

        if response.status_code != 200:
            return streams

        html = response.content.decode("utf-8")
        base_url = self._get_base_url(response.url)
        post_url = self._get_post_url(html, base_url)
        data = self._get_post_data(html, base_url)

        if post_url and data:
            streams_json = self._get_streams_data(post_url, data)
            streams = self._parse_streams(streams_json)

        return streams

    def _get_base_url(self, url):
        parsed_uri = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

        return domain

    def _get_post_url(self, html, base_url):
        for line in html.splitlines():
            if 'VB_POST_URL' in line:
                results = re.findall(r'\"(.+?)\"', line)

                if results:
                    return base_url + results[0]
                else:
                    return None

        return None

    def _get_post_data(self, html, base_url):
        results = re.findall(r'<script>.*?VB_TOKEN.*?=.*?"(.+?)";.*?VB_ID.*?=.*?"(.+?)";.*?<\/script>', html)
        if results:
            try:
                return  {
                    'VB_ID': results[0][1],
                    'VB_TOKEN': results[0][0],
                    'VB_NAME': ''
                }
            except Exception as e:
                cmn.error("Icdrama: " + str(e))
        else:
            results = re.findall(r'<script.+src="(.+\.vbjs\.html)".+decodeURIComponent\("(.+?)"\).+?R\[.+?\]\}\}\(''(.+?)''\).+(<\/script>|\/>)', html)
            try:
                key = results[0][2]
                key = key.replace("'", "")
                encrypted_string = unquote(results[0][1])
                decoded_result = ''

                for c in range(0, len(encrypted_string)):
                    code = ord(encrypted_string[c]) ^ ord(key[c % len(key)])
                    character = chr(code)
                    decoded_result = decoded_result + character

                data = decoded_result.split('~|.')
                return  {
                    'VB_ID': data[1],
                    'VB_TOKEN': data[0],
                    'VB_NAME': ''
                }
            except Exception as e:
                cmn.error("Icdrama: " + str(e))

        return None

    def _get_streams_data(self, url, data):
        # Make the ajax call
        session = requests.Session()

        self.headers['Referer'] = url
        self.headers['X-Requested-With'] = 'XMLHttpRequest'
        self.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

        response = session.post(url, data=data, headers=self.headers)
        if response.status_code != 200:
            return None

        #Band-aid fix. No idea what the first three characters are, but they are messing with the json. Removed them. - mugol
        json_content = response.content[3:]

        return json.loads(json_content)

    def _parse_streams(self, data):
        streams = []

        if data:
            strdecode = lambda s: base64.b64decode(unquote(s))
            exclude = ['Subtitles', 'image', 'JS', 'ADV']
            videos = [h for h in data if h['s'] not in exclude]
            streams = [(h['s'], strdecode(h['u'])) for h in videos]

        return streams

    def __method1(self, response):
        streams = []
        # Grab the HTML
        if response.status_code == 200:
            html = response.content.decode("utf-8")
            url  = response.url.decode("utf-8")
        else:
            # error, bail.
            return streams

        unobscured = None

        # Search for the obscured list of data, and decode.
        oblist = re.search(r"\[([\\\'xa-f0-9,]*)\]", html)
        if oblist:
            data = eval(oblist.group(0))
            for d in data:
                if len(d) > 10:
                    unobscured = self._unobscurify(d, 'V_TOKEN')
                    if unobscured:
                        break

        if not unobscured:
            # Might be in the dF
            df = re.search(r"dF\(('[\\xa-f0-9]*')\)", html)
            if df:
                obscured = eval(df.group(1))
                unobscured = self._unobscurify(obscured, 'V_TOKEN')

        # lol, maybe it's not obscured at all!
        for line in html.splitlines():
            if 'V_TOKEN' in line:
                unobscured = line
                break

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
        html = response.content.decode("utf-8")
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
        html = response.content.decode("utf-8")
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
            streams = list(zip(labels, urls))
        except Exception:
            pass
        return streams


    def __method4(self, response):
        ''' http://videobug.se/vid-al/XNkjCT5pBx1YlndruYWdWg?&caption=-sgCv7...
        '''
        html = response.content.decode("utf-8")
        streams = []
        vids = re.findall(r'''{ *file *: *strdecode\('(.+?)'\).*?label *: *"(.*?)"''', html)
        for cryptic_url, label in vids:
            url = base64.b64decode(unquote(cryptic_url)[::-1])
            streams.append((label, url))
        return streams


    def __method5(self, response):
        ''' http://videobug.se/vid/pVobcNozEWmTkarNnwX06w
        '''
        html = response.content.decode("utf-8")
        streams = []
        if jsunpack.detect(html):
            streams = self._extract_streams(jsunpack.unpack(html))
        return streams


    @classmethod
    def _is_enabled(cls):
        return True
