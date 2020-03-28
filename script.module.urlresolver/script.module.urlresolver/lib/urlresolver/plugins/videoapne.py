'''
    urlresolver Kodi plugin
    Copyright (C) 2019 gujal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re
from lib import helpers
from lib import jsunpack
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class VideoApneResolver(UrlResolver):
    name = "videoapne"
    domains = ["videoapne.co"]
    pattern = r'(?://|\.)(videoapne\.co)/(?:embed-)?([0-9a-zA-Z]+)'
    
    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA,
                   'Referer': 'http://bestinforoom.com/'}
        html = self.net.http_GET(web_url, headers=headers).content
        
        r = re.search("script'>(eval.*?)</script", html, re.DOTALL)
        
        if r:
            html = jsunpack.unpack(r.group(1))
            src = re.search(r'file:\s*"([^"]+m3u8)',html)
            if src:
                return src.group(1) + helpers.append_headers(headers)
        
        raise ResolverError('Video cannot be located.')

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='http://{host}/embed-{media_id}.html')