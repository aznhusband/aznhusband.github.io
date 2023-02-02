import os.path
from urllib.parse import urljoin
from lib.common import diritem, action_url, profile_dir

base_url = 'http://icdrama.to'
domains = ['hkdrama.to', 'adrama.to', 'icdrama.to', 'icdrama.se', 'adramas.se']
cache_file = os.path.join(profile_dir, 'cache.pickle')
store_file = os.path.join(profile_dir, 'store.pickle')

# the trailing forward slashes are necessary
# without it, page urls will be wrong (icdrama bug)
search_url = urljoin(base_url, '/search/%s/')
index_items = [
    diritem(33011, action_url('saved_list')),
    diritem(33000, action_url('recent_updates', url=urljoin(base_url, '/recently-updated/'))),
    diritem(33001, action_url('shows', url=urljoin(base_url, '/hk-drama/'))),
    diritem(33002, action_url('shows', url=urljoin(base_url, '/hk-movie/'))),
    diritem(33003, action_url('shows', url=urljoin(base_url, '/hk-show/'))),
    diritem(33004, action_url('shows', url=urljoin(base_url, '/chinese-drama/'))),
    diritem(33012, action_url('shows', url=urljoin(base_url, '/chinese-drama-cantonesedub/'))),
    diritem(33005, action_url('shows', url=urljoin(base_url, '/taiwanese-drama/'))),
    diritem(33013, action_url('shows', url=urljoin(base_url, '/taiwanese-drama-cantonesedub/'))),
    diritem(33006, action_url('shows', url=urljoin(base_url, '/korean-drama/'))),
    diritem(33014, action_url('shows', url=urljoin(base_url, '/korean-drama-cantonesedub/'))),
    diritem(33015, action_url('shows', url=urljoin(base_url, '/korean-drama-chinesesubtitles/'))),
    diritem(33007, action_url('shows', url=urljoin(base_url, '/korean-show/'))),
    diritem(33008, action_url('shows', url=urljoin(base_url, '/japanese-drama/'))),
    diritem(33016, action_url('shows', url=urljoin(base_url, '/japanese-drama-cantonesedub/'))),
    diritem(33017, action_url('shows', url=urljoin(base_url, '/japanese-drama-chinesesubtitles/'))),
    diritem(33009, action_url('shows', url=urljoin(base_url, '/movies/'))),
    diritem(33018, action_url('shows', url=urljoin(base_url, '/genre/25-animation.html'))),
    diritem(33010, action_url('search'))
]
