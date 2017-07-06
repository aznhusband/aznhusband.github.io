#!/usr/bin/python

import os

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def print_sizes(root):
    for name in sorted(os.listdir(root)):
        if name == 'index.html':
            continue
        print '<a href="%s">%s</a><td>%s</td>' % (name, name, sizeof_fmt(os.stat(name).st_size))


print_sizes('.')
