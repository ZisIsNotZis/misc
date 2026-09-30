#!/bin/env python
from os import listdir, stat
m = {}


def _(f):
    for i in listdir(f):
        F = f + '/' + i
        s = stat(F)
        if s.st_mode & 0o40000:
            _(F)
        else:
            i = i.rpartition('.')
            i = i[0] and i[2].lower()
            m[i] = m.get(i, 0) + s.st_size


_('.')
print(sorted(m.items(), key=lambda _: _[1]))
