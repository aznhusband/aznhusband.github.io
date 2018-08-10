import urllib
import sys
import xbmcplugin
import xbmcgui
import xml.etree.ElementTree as ET
import re
from urlresolver.lib.net import Net, get_ua
from urlresolver.hmf import HostedMediaFile
from urlparse import parse_qsl


baseurl = 'http://irss.se/dramas'


def log(s):
    xbmc.log(s, xbmc.LOGNOTICE)


def handleURL(url):
    log('url = ' + url)
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Vitamio/Android/4.0',
        'Cache-Control': 'no-cache',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Authorization-Key': '51c3ee8a1b27a7dcab000001',
        'X-Authorization-Secret': 'bdd442e8f1ff5dd0f3809195deb6d546'
    }

    xml = Net().http_GET(url, headers = headers).content.encode('UTF-8')
    #log(xml)
    tree = ET.fromstring(xml)

    url  = icon = title = None
    mode = '1'

    for element in tree.iter():
        if element.tag == 'item':
            addDir(url, icon, title, mode)
            url  = icon = title = None
            mode = '1'
        if element.tag == 'enclosure':
            url = element.attrib['url']
            if element.attrib['type'] != 'application/rss+xml':
                mode = '2'
            if element.attrib['type'] == 'video/mp4':
                mode = '3'
        if element.tag == 'link':
            url = element.text
        if element.tag == 'title':
            title = element.text
        if element.tag == 'description':
            icon = re.match(r"<img src='(.*)'", element.text).group(1)

    # Add the last one
    addDir(url, icon, title, mode)


def resolveVideo(url):
    import resolvers
    hmf = HostedMediaFile(url)
    vidurl = hmf.resolve()
    playVideo(vidurl)


def addDir(url, icon, title, mode):
    if url and title and mode:
        u = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + mode
        li = xbmcgui.ListItem(title, iconImage = 'DefaultVideo.png', thumbnailImage = icon)
        li.setInfo(type = 'Video', infoLabels = {'Title': title})
        return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = li, isFolder = True)


if __name__ == '__main__':
    handle = str(sys.argv[1])
    qs     = sys.argv[2]
    params = dict((k, urllib.unquote_plus(v)) for k, v in parse_qsl(qs.lstrip('?')))

    url  = None
    mode = None

    try:
        mode = params['mode']
        url  = params['url']
    except:
        pass

    if mode == None or url == None or len(url) < 1:
        handleURL(baseurl)
    elif mode == '1':
        handleURL(url)
    elif mode == '2':
        resolveVideo(url)
    elif mode == '3':
        xbmc.Player().play(url)

    xbmcplugin.endOfDirectory(int(handle))
