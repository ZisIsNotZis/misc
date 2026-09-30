#!/bin/env python3
from sys import argv
from json import JSONDecoder
from os.path import exists
from typing import Iterable
import re


def save(f: str, a: str, re=re.compile(r'\b.+?\b'), I=dict[str, int]()) -> None:
    f = _.group()[:64]if (_ := next(re.finditer(f), None))else ''
    for i in range(I.get(f, 0), 9999):
        if not exists(f'{f}{i}.txt'):
            I[f] = i+1
            open(f'{f}{i}.txt', 'w').write(a)
            return


def json(f: str) -> Iterable[dict]:
    f = open(f).read()
    d = JSONDecoder()
    while f:
        o, i = d.raw_decode(f)
        if isinstance(o, list):
            yield from o
        else:
            yield o
        f = f[i:]


for f in argv[1:]:
    for o in json(f):
        save(o.get('input') or o.get('output') or o['text'], o.get('output') or o.get('input') or o['text'])
