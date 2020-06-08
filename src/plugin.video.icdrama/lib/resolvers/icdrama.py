import re
import json
from urllib import unquote
from urlparse import urlparse
import base64
import requests
from bs4 import BeautifulSoup
import resolveurl
from resolveurl import common
from resolveurl.resolver import ResolveUrl, ResolverError
from resolveurl.plugins.lib import helpers

class Icdrama(ResolveUrl):
    name = 'Icdrama'
    domains = [ 'adrama.to', 'icdrama.se', 'icdrama.to']
    pattern = '(?://|\.)(adrama\.to|icdrama\.se|icdrama\.to)/(.+)'


    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):
        url = self.get_url(host, media_id)
        if 'vidembed' in url or 'vb.icdrama' in url:
            headers = self.headers
            headers['Referer'] = 'http://icdrama.to'

            response = requests.get(url, headers=headers)

            unwrapped_url = ''
            if 'videoredirect.php?' in url: #for current Openload source & other possible redirects
                unwrapped_url = response.url
            else:
                streams = self._extract_streams(response)
                unwrapped_url = helpers.pick_source(streams, auto_pick=False)

            if ('redirector.googlevideo.com' in unwrapped_url or
                'blogspot.com' in unwrapped_url or
                'fbcdn.net' in unwrapped_url): #for current Videobug source
                # Kodi can play directly, skip further resolve
                return unwrapped_url

            return resolveurl.resolve(unwrapped_url)
        else:
            try:
                html   = self.net.http_GET(url, headers=self.headers).content
                iframe = BeautifulSoup(html, 'html5lib').find('iframe')
                return resolveurl.resolve(iframe['src'])
            except:
                return None

    def _extract_streams(self, response):
        '''Return list of streams (tuples (url, label))
        '''
        streams = [] # list of tuples (url, label)

        methods = [self.__method6]
        for method in methods:
            streams = method(response)
            if streams:
                return streams
        raise ResolverError('Icdrama resolver: no streams found in ' + response.url)

    def __method6(self, response):
        streams = []

        if response.status_code != 200:
            return streams

        html = response.content
        post_url = self._get_post_url(html)
        data = self._get_post_data(html)

        if post_url and data:
            streams_json = self._get_streams_data(post_url, data)
            streams = self._parse_streams(streams_json)

        return streams

    def _get_post_url(self, html):
        for line in html.splitlines():
            if 'VB_POST_URL' in line:
                results = re.findall(r'\"(.+?)\"', line)

                if results:
                    return results[0]
                else:
                    return None

        return None

    def _get_post_data(self, html):
        results = re.findall(r'<script>.*?VB_TOKEN.*?=.*?"(.+?)";.*?VB_ID.*?=.*?"(.+?)";.*?<\/script>', html)
        if results:
            try:
                return  {
                    'VB_ID': results[0][1],
                    'VB_TOKEN': results[0][0],
                    'VB_NAME': ''
                }
            except Exception as e:
                common.logger.log_error("Icdrama: " + str(e))
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
                common.logger.log_error("Icdrama: " + str(e))

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

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'http://{host}/{media_id}')


    @classmethod
    def _is_enabled(cls):
        return True
