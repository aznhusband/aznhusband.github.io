#!/usr/bin/python

import os

def print_sizes(root):
    for name in sorted(os.listdir(root)):
        print '<a href="%s">%s</a><td>%d.0B</td>' % (name, name, os.stat(name).st_size)


print_sizes('.')
