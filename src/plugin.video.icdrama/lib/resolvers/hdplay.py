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
from .. import common as cmn

class HdPlay(ResolveUrl):
    name = 'HDplay'
    domains = [ 'hdplay.se']
    pattern = '(?://|\.)(hdplay\.se)/(.+)'


    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}


    def get_media_url(self, host, media_id):        
        url = self.get_url(host, media_id)
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return ""

        html = response.content        
        match = re.search(r'var\svideo_url\s?=\s?"(.+?)";', html)
        if match:
            video_url = 'http://' + host + match.group(1)
            return video_url + helpers.append_headers(self.headers)

        return ""

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, 'http://{host}/{media_id}')

    @classmethod
    def _is_enabled(cls):
        return True
