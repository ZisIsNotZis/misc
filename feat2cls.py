#!/bin/env python
from os import rename, listdir
from sklearn.linear_model import RidgeClassifier
import numpy as np

img = {}
for i in [i for i in listdir()if '.'not in i]+['.']:
    for j in listdir(i):
        if '.' not in j:
            continue
        j, k = j.rpartition('.')[::2]
        img.setdefault(j, [None, i, []])[2] += [k]
        if k == '384e':
            img[j][0] = np.fromfile(f'{i}/{j}.384e', 'e')
for i, j in zip(RidgeClassifier().fit(*zip(*[(v, i[:-1])for j, (v, i, k) in img.items()if i[-1] == '_'])).predict([v for j, (v, i, k) in img.items()if i[-1] != '_']), [j for j, (v, i, k) in img.items()if i[-1] != '_']):
    if i == img[j][1]:
        continue
    for k in img[j][2]:
        rename(f'{img[j][1]}/{j}.{k}', f'{i}/{j}.{k}')
    img[j][1] = i
