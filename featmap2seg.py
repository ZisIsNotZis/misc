#!/bin/env python
from sys import argv
from matplotlib.cm import rainbow
import cv2
import numpy as np

CVSI = CVSC = 0
CVSH = CVSW = 1
CLS = 4
EMBH = 30
EMBW = 7
IMGH = 416
IMGW = 104
X = np.empty((0, 384), 'f')
Y = np.empty(0, 'H')


def color(a: np.ndarray) -> np.ndarray:
    return np.multiply(rainbow(a/np.float32(CLS-1.))[..., :3], 128., dtype='f')


def append(a: np.ndarray, *i) -> None:
    print(*i)
    a[a.any(1).argmin()] = i


def strip(a: np.ndarray) -> np.ndarray:
    return a[:a.any(1).argmin()]


def norm(a: np.ndarray) -> np.ndarray:
    a /= np.linalg.norm(a, None, 2, True)
    return a


def Img(f: str) -> np.ndarray:
    return cv2.imread(f, cv2.IMREAD_GRAYSCALE)


def Emb(f: str) -> np.ndarray:
    return np.fromfile(f'{f.rsplit('.', 1)[0]}.{EMBH},{EMBW},384e', f'{EMBW},384e').astype('f')


def Lbl(f: str, w=False) -> np.ndarray | None:
    try:
        return np.memmap(f'{f.rsplit('.', 1)[0]}.99,3H', '3H')
    except FileNotFoundError:
        if w:
            return np.memmap(f'{f.rsplit('.', 1)[0]}.99,3H', '3H', 'w+', shape=99)


def Fit() -> None:
    global X, Y
    if _ := [(norm(cv2.resize(Emb(i), (IMGW, IMGH), 0, 0, 4))[*strip(j).T[:2]], strip(j)[:, 2])for i in argv for j in [Lbl(i)]if j is not None]:
        X, Y = map(np.concat, zip(*_))


def Prd(f: str) -> np.ndarray:
    if len(X):
        return Y[(norm(cv2.resize(Emb(f), (IMGW, IMGH), 0, 0, 4))@X.T).argmax(2)]
    return np.empty((IMGH, IMGW), 'B')


def Cvs(f: str) -> np.ndarray:
    return np.add(Img(f)[..., None] >> 1, color(Prd(f)), dtype='B', casting='unsafe')


def draw() -> None:
    Fit()
    cv2.imshow('lb', np.concat([np.concat(list(map(Cvs, argv[i:i+CVSW])), 1)for i in range(CVSI, CVSI+CVSH*CVSW, CVSW)]))


def cb(i: str | int, x=0, y=0, *_) -> None:
    global CVSI, CVSH, CVSW, CVSC
    match i:
        case '1':
            CVSC = 0 % CLS
        case '2':
            CVSC = 1 % CLS
        case '3':
            CVSC = 2 % CLS
        case '4':
            CVSC = 3 % CLS
        case 'w':
            if CVSH > 1:
                CVSH -= 1
                draw()
        case 's':
            if (CVSH + 1) * CVSW <= len(argv):
                CVSH += 1
                CVSI = min(CVSI, len(argv) - CVSH * CVSW)
                draw()
        case 'a':
            if CVSW > 1:
                CVSW -= 1
                draw()
        case 'd':
            if CVSH * (CVSW + 1) <= len(argv):
                CVSW += 1
                CVSI = min(CVSI, len(argv) - CVSH * CVSW)
                draw()
        case 'q':
            if CVSI > 0:
                CVSI = max(CVSI - CVSH * CVSW, 0)
                draw()
        case 'e':
            if CVSI < len(argv) - CVSH * CVSW:
                CVSI = min(CVSI + CVSH * CVSW, len(argv) - CVSH * CVSW)
                draw()
        case '\x1b':
            exit()
        case cv2.EVENT_LBUTTONDOWN:
            append(Lbl(argv[CVSI + y // 16 // EMBH * CVSW + x // 16 // EMBW], True), y % (EMBH * 16), x % (EMBW * 16), CVSC)
            draw()


del argv[0]
cv2.namedWindow('lb', cv2.WINDOW_GUI_NORMAL)
cv2.setMouseCallback('lb', cb)
draw()
while True:
    cb(chr(cv2.waitKey()))
