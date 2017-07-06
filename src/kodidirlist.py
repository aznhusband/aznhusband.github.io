#!/usr/bin/python

import os

def print_sizes(root):
    for name in sorted(os.listdir(root)):
        if name == 'index.html':
            continue
        print '<a href="%s">%s</a><td>%dB</td>' % (name, name, os.stat(name).st_size)


print_sizes('.')
