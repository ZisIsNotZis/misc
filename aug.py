#!/bin/env python
from sys import argv
from os import listdir, readlink, path, symlink
from multiprocessing import Pool
from random import shuffle
from PIL.Image import open, fromarray
import numpy as np


def f(dir: str) -> None:
    print(dir)
    img = listdir(dir)
    org = [_ for _ in img if not _.startswith('aug')]
    for i in shuffle(org) or org:
        try:
            I = readlink(f'{dir}/{i}')
        except OSError:
            I = i
        idir, _, I = I.rpartition('/')
        idir = idir or '.'
        for j in shuffle(_ := list(org)) or _:
            if len(img) >= 100:
                return
            ij = f'aug{i[:-5]}.{j}'
            if ij in img:
                continue
            try:
                J = readlink(f'{dir}/{j}')
            except OSError:
                J = j
            _, _, J = J.rpartition('/')
            IJ = f'{idir}/aug{I[:-5]}.{J}'
            if not path.exists(f'{dir}/{IJ}'):
                fromarray((np.asarray(open(f'{dir}/{i}')) >> 1) + (np.asarray(open(f'{dir}/{j}')) >> 1)).save(f'{dir}/{IJ}')
            symlink(IJ, f'{dir}/{ij}')
            img.append(f'{dir}/{ij}')


with Pool(28) as pool:
    pool.map(f, argv[1:])
