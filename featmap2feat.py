#!/bin/env python
from os import listdir
import numpy as np
import cv2

img = cv2.imread([i for i in listdir()if i[-5:] == '.webp'][0])
y, x, w, h = cv2.selectROI('', img)
cv2.destroyAllWindows()
sz = {}
for i in listdir():
    if i[-5:] != ',384e':
        continue
    i, _, j = i.rpartition('.')
    if np.dtype(j).itemsize > sz.get(i, 0):
        cv2.resize(np.fromfile(f'{i}.{j}', j)[0].astype('f'), img.shape[1::-1], 0, 0, cv2.INTER_LANCZOS4)[x:x+h, y:y+w].mean((0, 1)).astype('e').tofile(f'{i}.384e')
        sz[i] = np.dtype(j).itemsize
