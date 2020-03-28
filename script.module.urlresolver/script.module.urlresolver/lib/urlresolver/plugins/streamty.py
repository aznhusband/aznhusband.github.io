# -*- coding: utf-8 -*-
'''
    urlresolver Kodi plugin
    Copyright (C) 2018

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

class StreamtyResolver(UrlResolver):
    name = "streamty"
    domains = ["streamty.com"]
    pattern = '(?://|\.)(streamty\.com)/(?:embed-)?([0-9a-zA-Z]+)'

    def __init__(self):
        self.net = common.Net()

    def get_media_url(self, host, media_id):
        web_url = self.get_url(host, media_id)
        headers = {'User-Agent': common.RAND_UA, 'Referer': web_url}
        html = self.net.http_GET(web_url, headers=headers).content
        r = re.search("text/javascript'>(eval.*?)\s*</script>", html, re.DOTALL)
        if r:
            html = jsunpack.unpack(r.group(1))
            src = re.search('file:"([^"]+)"',html)
            if src:
                return src.group(1) + helpers.append_headers(headers)
        raise ResolverError('Video cannot be located.')
 
    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/embed-{media_id}.html')

