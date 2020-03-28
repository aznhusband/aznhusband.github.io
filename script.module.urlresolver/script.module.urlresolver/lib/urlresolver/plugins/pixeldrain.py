"""
    Kodi urlresolver plugin
    Copyright (C) 2019  script.module.urlresolver

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
"""
import json
from lib import helpers
from urlresolver import common
from urlresolver.resolver import UrlResolver, ResolverError

class PixelDrainResolver(UrlResolver):
    name = 'pixeldrain'
    domains = ['pixeldrain.com']
    pattern = '(?://|\.)(pixeldrain\.com)/(?:u|l)/([0-9a-zA-Z\-]+)'

    def __init__(self):
        self.net = common.Net()
        self.headers = {'User-Agent': common.RAND_UA}

    def get_host_and_id(self, url):
        self.web_url = url
        return super(PixelDrainResolver, self).get_host_and_id(url)

    def get_media_url(self, host, media_id):
        if( '/l/' in self.web_url ):
            response = self.get_media_url_list( host, media_id )
        else:
            response = self.get_media_url_file( host, media_id )
 
        if( response != False ):
            return response
        raise ResolverError('Unable to locate video')

    def get_media_url_file( self, host, media_id ):
        file_info = json.loads( self.net.http_GET('https://' + host + '/api/file/' + media_id + '/info', headers=self.headers).content )
        if( file_info['success'] == True and 'video' in file_info['mime_type'] ):
            return 'http://' + host + '/api/file/' + media_id
        return False

    def get_media_url_list( self, host, media_id ):
        file_list = json.loads( self.net.http_GET('https://' + host + '/api/list/' + media_id, headers=self.headers).content )
        if( file_list['success'] == True ):
            sources = []
            if( file_list['files'] ):
                for file in file_list['files']:
                    sources += [( file['name'], 'http://' + host + '/api/file/' + file['id'] )]
            return helpers.pick_source( sources, False )
        return False

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/u/{media_id}')
