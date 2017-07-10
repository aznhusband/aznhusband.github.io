import cPickle as pickle
from os import makedirs
from lib import config
from os.path import isfile, dirname, exists

def put(key, value):
    '''Store `value` to `key`
    Overwrites any existing value
    '''
    _put(key, value)


def get(key, default=None):
    '''Get value of `key` from store
    If `default` supplied,
        returns `default` if key not found
    Otherwise,
        raises KeyError if key not found
    '''
    try:
        return _get(key)
    except KeyError:
        if default is None:
            raise
        else:
            return default


def _put(key, value):
    store = _get_store()
    store[key] = value

    # create directory for store file if not exists
    parent = dirname(config.cache_file)
    if not exists(parent):
        makedirs(parent)

    with open(config.store_file, 'wb+') as f:
        pickle.dump(store, f)


def _get(key):
    store = _get_store()
    return store[key]


_store = None
def _get_store():
    global _store
    if _store is not None:
        return _store

    if isfile(config.store_file):
        with open(config.store_file, 'rb') as f:
            _store = pickle.load(f)
    else:
        _store = {}

    return _store
