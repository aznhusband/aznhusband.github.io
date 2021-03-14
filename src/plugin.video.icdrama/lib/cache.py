import functools
from . import config
from . import common
import pickle as pickle
from os import makedirs, remove
from datetime import datetime, timedelta
from os.path import isfile, dirname, exists

# Note: refrain from caching large results to persistent cache
def memoize(minutes=None):
    '''Simple function memoization
    (Only for module functions or singleton class methods)
    `minutes` - expire after this many minutes
                (None for non-persistent memoization)
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kargs):
            try:
                namespace = func.__module__
            except AttributeError:
                namespace = func.__self__.__class__

            full_func = '%s.%s' % (namespace, func.__name__)
            key = '%s(%s, %s)' % (full_func, args, kargs)

            try:
                out = _get(key)
            except KeyError:
                out = func(*args, **kargs)
                _put(key, out, minutes)
            return out
        return wrapped
    return decorator


def get(key):
    '''Get value of `key` from cache
    Raises KeyError if no such key
    '''
    return _get(key)

def put(key, value, minutes=60):
    '''Put `key`, `value` to cache
    Overwrites existing value if any
    Expires after `minutes` (default 60)
    `minutes` - None for non-persistent cache
                (in-memory cache)
    '''
    _put(key, value, minutes)


_nonpersist = {} # non-persistent cache
def _get(key):
    '''Get value of `key` from cache
    Tries non-persistent cache first
    Raises KeyError if no such key
    '''
    try:
        out = _nonpersist[key]
    except KeyError:
        cache = _get_cache()
        out = cache[key]
    return out


_expiries = '_expiries' # key for recording expiry times


def _put(key, value, minutes=60):
    '''Put `key`, `value` to cache
    Overwrites existing value if any
    Expires after `minutes`
    `minutes` - None for non-persistent cache
    '''
    if minutes is None:
        _nonpersist[key] = value
        return

    cache = _get_cache()
    cache[key] = value

    # check expiry
    try:
        key_exps = cache[_expiries]
    except KeyError:
        key_exps = cache[_expiries] = []
    now = datetime.now()
    key_exps.append((key, now+timedelta(minutes=minutes)))

    try:
        # create directory for cache file if not exists
        parent = dirname(config.cache_file)
        if not exists(parent):
            makedirs(parent)

        with open(config.cache_file, 'wb+') as f:
            pickle.dump(cache, f)
    except Exception:
        # TODO: log exception
        pass



_cache = None
def _get_cache():
    '''Lazy load cache file into variable `_cache`
    Returns `_cache` if already loaded
    '''
    global _cache
    if _cache is not None:
        return _cache

    if isfile(config.cache_file):
        try:
            with open(config.cache_file, 'rb') as f:
                _cache = pickle.load(f)
        except Exception:
            # if anything goes wrong, remove cache file
            try:
                remove(config.cache_file)
            except OSError:
                pass
            # TODO: log exception
            _cache = {}
        _clean(_cache)
    else:
        _cache = {}
    return _cache


def _clean(cache):
    '''Remove any expired values in `cache`
    '''
    key_exps = cache[_expiries]

    now = datetime.now()
    for k, e in key_exps:
        if now > e:
            cache.pop(k, 0)

    cache['_expiries'] = [(k, e) for k, e in key_exps if now <= e]
