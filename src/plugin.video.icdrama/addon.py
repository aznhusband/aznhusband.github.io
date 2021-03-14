from __future__ import absolute_import, division, unicode_literals
from future import standard_library
from future.builtins import *
standard_library.install_aliases()

import sys
from urllib.parse import parse_qsl
from urllib.parse import unquote
from lib import actions



if __name__ == '__main__':
    qs = sys.argv[2]
    kargs = dict((k, unquote(v))for k, v in parse_qsl(qs.lstrip('?')))

    action_name = kargs.pop('action', 'index') # popped
    if action_name in actions.actions:
        action_func = getattr(actions, action_name)
        action_func(**kargs)
    else:
        raise Exception('Invalid action: %s' % action_name)
