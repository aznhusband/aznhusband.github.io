#!/usr/bin/python

import os

def print_sizes(root):
    for name in sorted(os.listdir(root)):
        if name == 'index.html':
            continue
        print '<tr><td><a href="%s">%s</a></td><td>%dB</td></tr>' % (name, name, os.stat(name).st_size)


print '<html>'
print '<body>'
print '<table>'
print_sizes('.')
print '</table>'
print '</body>'
print '</html>'
