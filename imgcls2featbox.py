#!/bin/env python
from functools import reduce
from glob import glob
from itertools import starmap
from os import getenv, system, rename, remove
from sys import argv
from typing import Callable, Literal
from time import time

import numpy as np
import torch
from cv2 import imread, selectROI, createTrackbar, setTrackbarPos, imshow, getTrackbarPos, waitKey, destroyAllWindows, namedWindow
from halcon import himage_from_numpy_array, threshold, reduce_domain, region_features, concat_obj, union2, gen_rectangle1  # type: ignore
from yaml import safe_load, SafeDumper, dump_all


class FlowDumper(SafeDumper):
    def represent_sequence(s, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, True)


def chk[**P, T](f: Callable[P, T], *arg: P.args, **kwarg: P.kwargs) -> T:
    t = f(*arg, **kwarg)
    assert t is not None, (f, arg, kwarg)
    return t


def getfeat(img: np.ndarray, roi: list[tuple[int, int, int, int]], thres: tuple[int, int], featid: list[str]) -> np.ndarray:
    feat = np.array(region_features(threshold(reduce_domain(reduce(concat_obj, map(himage_from_numpy_array, img)), reduce(union2, starmap(gen_rectangle1, roi))), *thres), featid), 'f').reshape(len(img), -1)
    feat[:, [i for i, j in enumerate(featid) if j == 'row']] = img.shape[1] - feat[:, [i for i, j in enumerate(featid) if j == 'row']]
    feat[:, [i for i, j in enumerate(featid) if j == 'phi']] = (feat[:, [i for i, j in enumerate(featid) if j == 'phi']] + np.pi) % np.pi - np.pi / 2
    return feat


def fitboxlp(FEAT: np.ndarray[tuple[int, int], np.dtype[np.float32]], nok: int, time: int, eps=1e-4) -> np.ndarray[tuple[Literal[2], int], np.dtype[np.float32]]:
    from pulp import LpProblem, LpMinimize, LpVariable, lpSum, PULP_CBC_CMD, value  # type: ignore
    """
    # sample*feat -> 2*feat
    """
    PRB = LpProblem("BOX", LpMinimize)
    # low bound, per feature
    L = list(LpVariable.dict("L", range(FEAT.shape[1]), cat="Continuous").values())
    # up bound, per feature
    U = list(LpVariable.dict("U", range(FEAT.shape[1]), cat="Continuous").values())
    # whether some sample is invalid, per sample
    INVALID = list(LpVariable.dict("INVALID", range(len(FEAT)), cat="Binary").values())
    # whether some ng feature is in, to the left, or to the right of the box, per ng sample per feature
    # since plup does not support Trinary category, we use NGIN to indicate in, and NGLEFT to indicate left
    NGIN = [list(LpVariable.dict(f"NGIN{i}", range(FEAT.shape[1]), cat="Binary").values())for i in range(len(FEAT)-nok)]
    NGLEFT = [list(LpVariable.dict(f"NGLEFT{i}", range(FEAT.shape[1]), cat="Binary").values())for i in range(len(FEAT)-nok)]
    # minimize invalid ratio, scaled for unbalanced data
    PRB += lpSum(INVALID[:nok])/(nok+eps) + lpSum(INVALID[nok:])/(len(FEAT)-nok+eps)
    # big enough constant, per feature
    BIG = FEAT.max(0)-FEAT.min(0)+1
    # all valid ok should be in box
    for feats, invalid in zip(FEAT[:nok], INVALID):
        for feat, l, u, big in zip(feats, L, U, BIG):
            big = big*invalid
            # must be true if invalid
            PRB += l <= feat-eps + big
            PRB += feat+eps <= u + big
    # all valid ng should have at least one feature out of box
    for feats, invalid, ngins, nglefts in zip(FEAT[nok:], INVALID[nok:], NGIN, NGLEFT):
        PRB += lpSum(ngins)+1 <= len(ngins) + invalid
        # ngin and ngleft should match fact
        for feat, l, u, ngin, ngleft, big in zip(feats, L, U, ngins, nglefts, BIG):
            ngin = ngin+invalid
            # must be true if invalid or in or not left (i.e. right)
            PRB += feat+eps <= l + big*(ngin+1-ngleft)
            PRB += u <= feat-eps + big*(ngin+ngleft)
    PRB.solve(PULP_CBC_CMD(msg=0, timeLimit=time, threads=28))
    return np.array([list(map(value, i))for i in [L, U]])


def fitboxnn(feat: torch.Tensor, nok: int, batch=0, lr=.1, k=torch.logspace(0, 2.5, 100), wd=1e-5) -> np.ndarray[tuple[Literal[2], int], np.dtype[np.float32]]:
    feat = torch.as_tensor(feat)
    feat = feat-(mean := feat.mean(0))
    feat /= (std := feat.std(0))+1e-9
    batch = batch or 4*2**feat.shape[1]
    l, u = torch.randn(2, batch, 1, feat.shape[1]).sort(0)[0]
    l.requires_grad_(True)
    u.requires_grad_(True)
    o = torch.optim.AdamW([l, u], lr, weight_decay=wd)
    for j, k in enumerate(k):
        o.zero_grad()
        logp = torch.nn.functional.logsigmoid((feat-l)*k).sum(2)+torch.nn.functional.logsigmoid((u-feat)*k).sum(2)
        logp = logp[:, :nok].mean()+(1e-9-logp[:, nok:].expm1()).log().mean(0).sum(0)/(len(feat)-nok+1e-9)
        (-logp).backward()
        o.step()
    cls = ((l <= feat) & (feat <= u)).all(2)
    okok = cls[:, :nok].mean(1, dtype=torch.float)
    ngok = cls[:, nok:].sum(1, dtype=torch.float)/(len(feat)-nok+1e-9)
    i = (okok-ngok).argmax()
    return (torch.stack([l.data[i, 0], u.data[i, 0]])*std+mean).numpy()


def optbox(feat: np.ndarray, box: np.ndarray) -> np.ndarray:
    return np.stack([(feat[(box-1).clip(0)]+feat[box.clip(max=len(feat)-1)])/2 for feat, box in zip(np.sort(feat.T), box.T)for box in [feat.searchsorted(box)]], 1)


def getroi(img: np.ndarray, roi: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    img = img.mean(0, 'f').astype('B')[..., None].repeat(3, 2)
    for x, y, X, Y in roi:
        img[x:X, y:Y:Y - y - 1, 2] = img[x:X:X - x - 1, y:Y, 2] = 255
    for i in range(2):
        y, x, Y, X = selectROI(WND, img, printNotice=False)
        destroyAllWindows()
        if Y:
            roi[i:] = (x, y, x + X, y + Y),
        elif not roi[i:]:
            break
    return roi


def getthres(file: list[str], img: np.ndarray, nok: list[int], roi: list[tuple[int, int, int, int]], thres: tuple[int, int], cb: Callable[[tuple[int, int]], None]) -> tuple[int, int] | None:
    def cb_(_):
        n = getTrackbarPos('n', WND)
        tmp = img[n, ..., None].repeat(3, 2)
        for x, y, X, Y in roi:
            mask = (getTrackbarPos('i', WND) <= tmp[x:X, y:Y, 0]) & (tmp[x:X, y:Y, 0] <= getTrackbarPos('j', WND))
            tmp[x:X, y:Y][mask] >>= 1
            tmp[x:X, y:Y, 2][mask] |= 128
        x, y, X, Y = (f(i) for f, i in zip((min, min, max, max), zip(*roi)))
        imshow(WND, tmp[x:X, y:Y])

    n = 0
    while True:
        cb(thres)
        namedWindow(WND)
        createTrackbar('n', WND, 0, len(img) - 1, cb_)
        setTrackbarPos('n', WND, n)
        createTrackbar('i', WND, 0, 255, cb_)
        setTrackbarPos('i', WND, thres[0])
        createTrackbar('j', WND, 0, 255, cb_)
        setTrackbarPos('j', WND, thres[1])
        try:
            match (chr(waitKey()), n := getTrackbarPos('n', WND), thres := (getTrackbarPos('i', WND), getTrackbarPos('j', WND)))[0]:
                case 'c':
                    return thres
                case 'r':
                    return None
                case '\x1b':
                    exit()
                case 'o':
                    system(f'xdg-open {n}')
                case 'x':
                    if n < nok[0]:
                        rename(file[n], file[n].replace('/OK/', '/NG/'))
                        nok[0] -= 1
                        file[n], file[nok[0]] = file[nok[0]], file[n].replace('/OK/', '/NG/')
                        img[n], img[nok[0]] = img[nok[0]], img[n]
                    else:
                        rename(file[n], file[n].replace('/NG/', '/OK/'))
                        file[n], file[nok[0]] = file[nok[0]], file[n].replace('/NG/', '/OK/')
                        img[n], img[nok[0]] = img[nok[0]], img[n]
                        nok[0] += 1
                case 'd':
                    if n < nok[0]:
                        remove(file[n])
                        nok[0] -= 1
                        file[n], file[nok[0]] = file[nok[0]], file[-1]
                        del file[-1]
                        img[n], img[nok[0]] = img[nok[0]], img[-1]
                        img = img[:-1]
                    else:
                        remove(file[n])
                        file[n] = file[-1]
                        del file[-1]
                        img[n] = img[-1]
                        img = img[:-1]
        finally:
            destroyAllWindows()


def fit(stage: str, task: str, featid: list[str]):
    global WND
    try:
        cfg = safe_load(open(f'{stage}.{task}.yml')) or {}
    except:
        cfg = {}
    rectangle1_domain = cfg.get('rectangle1_domain', [])
    threshold = cfg.get('threshold', (128, 255))
    okok = cfg.get('_okok', 0)
    ngok = cfg.get('_ngok', 100)
    feat = np.array(cfg.get('_feat', []))
    if getenv('LOAD', 'LOW') == 'LOW' and okok >= 40 and ngok <= 60:
        return
    file = glob(f'{stage}/{task}/OK/*.webp')
    nok = [len(file)]
    file += glob(f'{stage}/{task}/NG/*.webp')
    if not file:
        return
    if not nok[0]:
        print(stage, task, 'no ok')
        return
    img = np.stack([chk(imread, i).mean(2, 'f').astype('B') for i in file])
    box = np.empty((2, 0))

    def cb(thres: tuple[int, int]):
        global WND
        nonlocal feat, box, okok, ngok
        if rectangle1_domain:
            feat = getfeat(img, rectangle1_domain, thres, featid)
            if getenv('DBG'):
                print(featid)
                list(starmap(print, zip(range(len(file)), file, feat)))
            if len(feat) > nok[0]:
                # t = time()
                # box = fitboxlp(feat, nok[0], getenv('MAX',10))
                # res = (box[0] <= feat).all(1) & (feat <= box[1]).all(1)
                # okok = int((res[:nok[0]].sum() + 1e-9) / (nok[0] + 1e-9) * 100)
                # ngok = int(res[nok[0]:].sum() / (len(img) - nok[0] + 1e-9) * 100)
                # if time()-t > getenv('MAX',10)//2:
                box = fitboxnn(feat, nok[0])
                res = (box[0] <= feat).all(1) & (feat <= box[1]).all(1)
                okok = int((res[:nok[0]].sum() + 1e-9) / (nok[0] + 1e-9) * 100)
                ngok = int(res[nok[0]:].sum() / (len(img) - nok[0] + 1e-9) * 100)
                #     print(okok, ngok, okok2, ngok2)
                #     if okok2 - ngok2 > okok - ngok:
                #         box = box2
                #         okok = okok2
                #         ngok = ngok2
                # else:
                #     print(okok, ngok)
            else:
                ma = feat.max(0)
                mi = feat.min(0)
                box = np.stack([mi-(ma-mi)*.2, ma+(ma-mi)*.2])
                okok = 100
                ngok = 0
        else:
            okok = 0
            ngok = 100
        WND = f'{okok} {ngok} {nok[0]} {task} {stage}'

    WND = f'{okok} {ngok} {nok[0]} {task} {stage}'
    if getenv('UI', 'LOW') != 'ALL':
        cb(threshold)
    if getenv('UI', 'LOW') == 'ALL' or (getenv('UI', 'LOW') == 'LOW' and (okok < 40 or ngok > 60)):
        while True:
            rectangle1_domain = getroi(img, rectangle1_domain)
            if (_ := getthres(file, img, nok, rectangle1_domain, threshold, cb)):
                threshold = _
                break
    print(stage, task, nok[0], len(file)-nok[0], okok, ngok)
    dump_all([{
        'rectangle1_domain': rectangle1_domain,
        'threshold': threshold,
        '_nok': nok[0],
        '_nng': len(img)-nok[0],
        '_h': img.shape[1],
        '_w': img.shape[2],
        '_avg': img.mean(dtype='f').item(),
        '_std': img.std(dtype='f').item(),
        '_okok': okok,
        '_ngok': ngok,
        '_file': ' '.join(i.split('/')[-1][:-5]for i in file),
        '_feat': ' '.join(str(float('%.4e' % i)).strip('0').rstrip('.')for i in feat.ravel()),
    } | dict(zip(featid, box.T.tolist()))], open(f'{stage}.{task}.yml', 'w'), Dumper=FlowDumper, sort_keys=False, width=999999)


WND = ''
for stage in argv[1:]:
    stage, task = stage.split('/')[:2]
    fit(stage, task, {'NOZLE': ['row', 'column', 'height', 'width', 'area', 'phi', 'ra', 'rb'], 'SB': ['row', 'height'], 'DIRT': ['area'], 'FLOW': ['width', 'area'], 'FLOW2': ['ra', 'rb', 'phi']}[task])
