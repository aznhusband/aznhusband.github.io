import xbmc
import xbmcgui
import urllib.request, urllib.parse, urllib.error
import functools
import xbmcaddon
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from resolveurl.resolver import ResolverError
from resolveurl.lib.net import get_ua
from lib import config, common, scrapers, store, cleanstring, cache, auto_select

actions = []
def _action(func):
    '''Decorator
    Mark the function as a valid action by
    putting the name of `func` into `actions`
    '''
    actions.append(func.__name__)
    return func

def _dir_action(func):
    '''Decorator
    Assumes `func` returns list of diritems
    Results from calling `func` are used to build plugin directory
    '''
    @_action # Note: must keep this order to get func name
    @functools.wraps(func)
    def make_dir(*args, **kargs):
        diritems = func(*args, **kargs)
        if not diritems:
            return
        for di in diritems:
            common.add_item(di)
        common.end_dir()
    return make_dir

@_dir_action
def index():
    return config.index_items

def _saved_to_list_context_menu(eng_name, ori_name, show_url, image):
    add_save_url = common.action_url('add_to_saved', eng_name=eng_name, ori_name=ori_name,
                                     show_url=show_url, image=image)
    builtin_url = common.run_plugin_builtin_url(add_save_url)
    context_menu = [(xbmcaddon.Addon().getLocalizedString(33108), builtin_url)]
    return context_menu

@_dir_action
def shows(url):
    di_list = []
    for eng_name, ori_name, show_url, image in scrapers.shows(url):
        action_url = common.action_url('versions', url=show_url)
        name = cleanstring.show(eng_name, ori_name)
        cm = _saved_to_list_context_menu(eng_name, ori_name, show_url, image)
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))
    for page, page_url in scrapers.pages(url):
        action_url = common.action_url('shows', url=page_url)
        page_label = cleanstring.page(page)
        di_list.append(common.diritem(page_label, action_url))
    return di_list

@_dir_action
def recent_updates(url):
    di_list = []
    for name, update_url in scrapers.recent_updates(url):
        action_url = common.action_url('mirrors', url=update_url)
        di_list.append(common.diritem(name, action_url))
    return di_list

@_dir_action
def versions(url):
    versions = scrapers.versions(url)
    if len(versions) == 1:
        ver, href = versions[0]
        return _episodes(href)
    else:
        di_list = []
        for label, version_url in versions:
            action_url = common.action_url('episodes', url=version_url)
            ver = cleanstring.version(label)
            di_list.append(common.diritem(ver, action_url))

            if auto_select.settings_is_set('auto_select_version'):
                desire_version = auto_select.get_version_string()
                if desire_version != '' and desire_version in ver.lower():
                    common.notify(
                        heading="Auto picked version",
                        message="Picked {}".format(ver))
                    return _episodes(versions[0][1])

        return di_list

@_dir_action
def episodes(url):
    return _episodes(url)

def _episodes(url):
    episodes = scrapers.episodes(url)
    if len(episodes) > 0:
        di_list = []
        for name, episode_url in episodes:
            action_url = common.action_url('mirrors', url=episode_url)
            epi = cleanstring.episode(name)
            di_list.append(common.diritem(epi, action_url, isfolder=False, isplayable=True))
        return di_list
    else:
        return _mirrors(url)

@_dir_action
def search(url=None):
    if not url:
        heading = xbmcaddon.Addon().getLocalizedString(33301)
        s = common.input(heading)
        if s:
            url = config.search_url % urllib.parse.quote(s.encode('utf8'))
        else:
            return []
    di_list = []
    for eng_name, ori_name, show_url, image in scrapers.search(url):
        action_url = common.action_url('versions', url=show_url)
        name = cleanstring.show(eng_name, ori_name)
        cm = _saved_to_list_context_menu(eng_name, ori_name, show_url, image)
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))
    for page, page_url in scrapers.pages(url):
        action_url = common.action_url('search', url=page_url)
        page_label = cleanstring.page(page)
        di_list.append(common.diritem(page_label, action_url))
    if not di_list:
        common.popup(xbmcaddon.Addon().getLocalizedString(33304))
    return di_list


_saved_list_key = 'saved_list'
def _get_saved_list():
    try:
        return store.get(_saved_list_key)
    except KeyError:
        pass
    try: # backward compatible (try cache)
        return cache.get(_saved_list_key)
    except KeyError:
        return []


@_dir_action
def saved_list():
    sl = _get_saved_list()
    di_list = []
    for eng_name, ori_name, show_url, image in sl:
        action_url = common.action_url('versions', url=show_url)
        name = cleanstring.show(eng_name, ori_name)
        remove_save_url = common.action_url('remove_saved', eng_name=eng_name, ori_name=ori_name,
                                            show_url=show_url, image=image)
        builtin_url = common.run_plugin_builtin_url(remove_save_url)
        cm = [(xbmcaddon.Addon().getLocalizedString(33109), builtin_url)]
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))
    return di_list

@_action
def add_to_saved(eng_name, ori_name, show_url, image):
    with common.busy_indicator():
        sl = _get_saved_list()
        sl.insert(0, (eng_name, ori_name, show_url, image))
        uniq = set()
        sl = [x for x in sl if not (x in uniq or uniq.add(x))]
        store.put(_saved_list_key, sl)
    common.popup(xbmcaddon.Addon().getLocalizedString(33302))

@_action
def remove_saved(eng_name, ori_name, show_url, image):
    sl = _get_saved_list()
    sl.remove((eng_name, ori_name, show_url, image))
    store.put(_saved_list_key, sl)
    common.refresh()
    common.popup(xbmcaddon.Addon().getLocalizedString(33303))

@_action
def play_mirror(url):
    with common.busy_indicator():
        soup = BeautifulSoup(common.webread(url), 'html5lib')
        iframe = soup.find(id='iframeplayer')
        iframe_url = urljoin(config.base_url, str(iframe.attrs['src']))
        try:
            vidurl = common.resolve(iframe_url)
        except ResolverError as e:
            if str(e) == 'No link selected':
                return
            raise  e


        if vidurl:
            try:
                title, image = scrapers.title_image(url)
            except Exception:
                # we can proceed without the title and image
                title, image = ('', '')
            li = xbmcgui.ListItem(title)
            li.setArt({'thumb': image})
            if 'User-Agent=' not in vidurl:
                vidurl = vidurl + '|User-Agent=' + urllib.parse.quote(get_ua())
            li.setPath(vidurl)
            common.play_video(li)

        else:
            common.notify(
                heading="icDrama",
                message="Unable to play video")
@_dir_action
def mirrors(url):
    return _mirrors(url)

def _mirrors(url):
    mirrors = scrapers.mirrors(url)
    num_mirrors = len(mirrors)
    if num_mirrors > 0:
        di_list = []
        for mirr_label, parts in mirrors:
            for part_label, part_url in parts:
                label = cleanstring.mirror(mirr_label, part_label)
                action_url = common.action_url('play_mirror', url=part_url)
                di_list.append(common.diritem(label, action_url, isfolder=False))

        if auto_select.settings_is_set('auto_select_first_mirror'):
            common.notify(
                heading="Other mirrors exists",
                message=", ".join("{} (count: {})".format(mirr_label, len(parts)) for mirr_label, parts in mirrors),
                time=6000)
            play_mirror(url)
        return di_list
    else:
        # if no mirror listing, try to resolve this page directly
        play_mirror(url)
        return []
