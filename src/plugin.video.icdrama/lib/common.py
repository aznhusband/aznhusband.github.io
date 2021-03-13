import sys
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
from contextlib import contextmanager
from os.path import abspath, dirname
from urllib.parse import urlencode, quote
from resolveurl.hmf import HostedMediaFile
import resolveurl
from resolveurl.lib.net import Net, get_ua

_plugin_url = sys.argv[0]
_handle = int(sys.argv[1])
_dialog = xbmcgui.Dialog()

if hasattr(xbmcvfs, 'translatePath'):
    profile_dir = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
else:
    profile_dir = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))


def debug(s):
    xbmc.log(str(s), xbmc.LOGDEBUG)

def error(s):
    xbmc.log(str(s), xbmc.LOGERROR)

def webread(url):
    if type(url) is str:
        url = url.encode('utf8')
    url = quote(url, ':/')

    net = Net()
    headers = {'User-Agent': get_ua()}
    return net.http_GET(url, headers=headers).content

def action_url(action, **action_args):
    action_args['action'] = action
    for k, v in list(action_args.items()):
        if type(v) is str:
            action_args[k] = v.encode('utf8')
    qs = urlencode(action_args)
    return _plugin_url + '?' + qs

def add_item(diritem):
    xbmcplugin.addDirectoryItem(**diritem)

def end_dir():
    xbmcplugin.endOfDirectory(_handle)

def diritem(label_or_stringid, url, image='', isfolder=True, context_menu=[]):
    if type(label_or_stringid) is int:
        label = xbmcaddon.Addon().getLocalizedString(label_or_stringid)
    else:
        label = label_or_stringid
    listitem = xbmcgui.ListItem(label)
    listitem.setArt({'icon': image})
    listitem.addContextMenuItems(context_menu, replaceItems=True)
    # this is unpackable for xbmcplugin.addDirectoryItem
    return dict(
        handle   = _handle,
        url      = url,
        listitem = listitem,
        isFolder = isfolder
    )

def popup(s):
    addon_name = xbmcaddon.Addon().getAddonInfo('name')
    try:
        # Gotham (13.0) and later
        _dialog.notification(addon_name, s)
    except AttributeError:
        _dialog.ok(addon_name, s)

def select(heading, options):
    return _dialog.select(heading, options)

def resolve(url):
    if type(url) is str:
        url = url.encode('utf8')
    url = quote(url, ':/')

    # import the resolvers so that resolveurls pick them up
    import lib.resolvers
    hmf = HostedMediaFile(url)
    if hmf:
        return hmf.resolve()
    else:
        return ""

def sleep(ms):
    xbmc.sleep(ms)

def back_dir():
    # back one directory
    xbmc.executebuiltin('Action(ParentDir)')

def refresh():
    # refresh directory
    xbmc.executebuiltin('Container.Refresh')

def run_plugin(url):
    xbmc.executebuiltin(run_plugin_builtin_url(url))

def run_plugin_builtin_url(url):
    return 'RunPlugin(%s)' % url

def input(heading):
    kb = xbmc.Keyboard(default='', heading=heading)
    kb.doModal()
    if kb.isConfirmed():
        return kb.getText()
    return None

@contextmanager
def busy_indicator():
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialog)')
