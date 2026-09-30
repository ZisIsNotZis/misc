#!/bin/env python3.12
import functools
import glob
import os
import subprocess
import sys
import typing

import cv2
import halcon as ha
import numpy as np
import pulp
import yaml
from halcon import reduce_domain
from torch.nn.functional import threshold


class FlowDumper(yaml.SafeDumper):
    def represent_sequence(s, tag, sequence, flow_style=None):
        return super().represent_sequence(tag, sequence, True)


def read(f):
    return np.frombuffer(subprocess.Popen(f"ffmpeg -v 0 -c h264_qsv -i {f} -f rawvideo -pix_fmt gray -".split(),
                                          stdout=-1).stdout.read(), ','.join(
        subprocess.Popen(f"ffprobe -v 0 -show_entries stream=height,width -of csv=p=0 {f}".split(), stdout=-1,
                         text=True).stdout.read()[:-1].split(',')[::-1]) + 'B') if f.endswith('mp4') else \
        cv2.imread(f, cv2.IMREAD_GRAYSCALE)[None]


def fitbox(X, N):
    prb = pulp.LpProblem("fitbox", pulp.LpMaximize)
    L = pulp.LpVariable.dicts("l", range(X.shape[1]), cat="Continuous")
    U = pulp.LpVariable.dicts("u", range(X.shape[1]), cat="Continuous")
    A = pulp.LpVariable.dicts("a", range(N), cat="Binary")
    B = pulp.LpVariable.dicts("b", range(len(X) - N), cat="Binary")
    prb += pulp.lpSum(A.values()) / (N + 1e-19) - pulp.lpSum(B.values()) / (len(X) - N + 1e-9)
    max = X.max() - X.min() + 1
    for x, a in zip(X, A.values()):
        for x, l, u in zip(x, L.values(), U.values()):
            prb += l <= x + max * (1 - a)
            prb += x <= u + max * (1 - a)
    for x, b in zip(X[N:], B.values()):
        for x, l, u in zip(x, L.values(), U.values()):
            prb += l <= x + max * (1 - b)
            prb += x <= u + max * (1 - b)
    prb.solve(pulp.PULP_CBC_CMD(msg=False))
    return np.array([list(map(pulp.value, i.values())) for i in [L, U]]) + [[-1e-5], [1e-5]]


def tunebox(x, i):
    return np.stack(
        [(np.where(i, x[i - 1], 2 * x[0] - x[-1]) + np.where(i < len(x), x[i % len(x)], x[-1] * 2 - x[0])) / 2 for x, i
         in zip(np.sort(x.T), i.T) for i in [np.searchsorted(x, i)]], 1)


def zoom(a):
    k = (np.array([1024, 1920]) // a.shape[:2]).min()
    return a.repeat(k, 0).repeat(k, 1), int(k)


def getitem(a, i, _=None):
    try:
        return a[i]
    except IndexError:
        return _


def setitem(a, i, _):
    if i < len(a):
        a[i] = _
    else:
        a += (_,)


def features(imgs: ha.HObject, roi: ha.HObject, thres: list[float], feats: list[str]) -> np.ndarray:
    imgs = ha.gamma_image(imgs, 1.1 ** gamma, 0, 0, 255, 'true')
    grayfeats = (_ := [i[4:] for i in feats if i.startswith('gray')]) and [ha.gray_features(roi, i, _) for i in (
        imgs if thres[0] < thres[1] else ha.invert_image(imgs))]
    sobelfeats = (_ := [i[5:] for i in feats if i.startswith('sobel')]) and [ha.gray_features(roi, i, _) for i in
                                                                             ha.sobel_amp(imgs, 'sum_abs', 3)]
    feats = (_ := [i for i in feats if not i.startswith('gray') and not i.startswith('sobel')]) and np.reshape(
        ha.region_features(ha.threshold(ha.reduce_domain(imgs, roi), *thres), _), (-1, len(_)))
    feats = np.concat([i for i in (feats, grayfeats, sobelfeats) if len(i)], 1)
    feats[:, _] = ha.get_image_size(imgs)[1][0] - feats[:, (_ := [i for i, _ in enumerate(featids) if 'row' in _])]
    feats[:, _] = (feats[:, (_ := [i for i, _ in enumerate(featids) if 'phi' in _])] + np.pi) % np.pi - np.pi / 2
    return feats


def draw(_=None):
    gamma = cv2.getTrackbarPos('gamma', wnd) - 50
    threshold = sorted((cv2.getTrackbarPos('min', wnd), cv2.getTrackbarPos('max', wnd)))
    i = cv2.getTrackbarPos('i', wnd)
    rgb = ha.gamma_image(ha.crop_domain(ha.reduce_domain(ha.himage_from_numpy_array(img[i, ..., None].repeat(3, 2)),
                                                         functools.reduce(ha.union2, (ha.gen_rectangle1(*i) for i in
                                                                                      rectangle1_domain)))),
                         1.1 ** gamma, 0, 0, 255, 'true')
    ha.overpaint_region(rgb, ha.threshold(rgb, *threshold), [0, 0, 255], 'fill')
    ha.overpaint_region(rgb, ha.gen_rectangle1(0, 0, 2, 2), [0, 255, 0] if res[i] == (i < _nok) else [0, 0, 255],
                        'fill')
    cv2.imshow(wnd, ha.himage_as_numpy_array(
        ha.zoom_image_factor(rgb, *[float(min(np.divide([1920, 1000], ha.get_image_size_s(rgb))))] * 2, 'constant')))


def calcbox():
    global feats, box, res, _okok, _ngok
    tmp = functools.reduce(ha.concat_obj, map(ha.himage_from_numpy_array, img))
    roi = functools.reduce(ha.union2, [ha.gen_rectangle1(*i) for i in rectangle1_domain])
    feats = features(tmp, roi, threshold, featids)
    box = fitbox(feats, _nok)
    box = tunebox(feats, box)
    res = (box[0] <= feats).all(1) & (feats <= box[1]).all(1)
    _okok = round(res[:_nok].sum() / (_nok + 1e-19) * 100)
    _ngok = round(res[_nok:].sum() / (_nng + 1e-19) * 100)


def calcbase():
    global base
    base = feats[:_nok].mean(0)
    if task == 'SB':
        base[[i for i, _ in enumerate(featids) if 'row' in _]] = img.shape[1] - rectangle1_domain[0][2]


LOAD: typing.Literal['ALL', 'LOW', 'EMPTY'] = os.getenv('LOAD', 'ALL')
UI: typing.Literal['ALL', 'LOW', 'EMPTY', 'NONE'] = os.getenv('UI', 'ALL')
cv2.startWindowThread()
for stage in sys.argv[1:]:
    stage = stage.rstrip('/')
    for task, featids in dict(NOZLE='row column area phi'.split(), SB='row height'.split(), DIRT=['area'],
                              FLOW=['width'], FLOW2=['ra', 'rb', 'phi']).items():
        try:
            cfg = yaml.safe_load(open(f'{stage}.{task}.yml')) or {}
        except FileNotFoundError:
            cfg = {}
        rectangle1_domain, threshold, gamma, _okok, _ngok = [cfg.get(i, j) for i, j in
                                                             zip('rectangle1_domain,threshold,gamma,_okok,_ngok'.split(
                                                                 ','), [[(0, 0, 1000, 1000)], [0, 128], 0, 0, 0])]
        if not (LOAD == 'ALL' or (LOAD == 'LOW' and (_okok < 90 or _ngok > 10)) or (
                LOAD == 'EMPTY' and (not rectangle1_domain or threshold == [128, 255]))):
            continue
        try:
            file = list(map(glob.glob, [f'{stage}/{task}/OK/*', f'{stage}/{task}/NG/*']))
        except FileNotFoundError:
            continue
        _nok, _nng = map(len, file)
        if not _nok:
            if _nng:
                print(stage, task, 'NOOK')
            continue
        file = sum(file, [])
        img = np.concat(list(map(read, file)))
        _h, _w = img.shape[1:]
        calcbox()
        while UI == 'ALL' or (UI == 'LOW' and (_okok < 90 or _ngok > 10)) or (
                UI == 'EMPTY' and (not rectangle1_domain or threshold == [128, 255])):
            i = 0
            wnd = f'{stage}{task}{_nok}/{_nng} {i}/{len(rectangle1_domain)}'
            cv2.namedWindow(wnd)
            while True:
                tmp = (img.mean(0, dtype='f') / 255)[..., None].repeat(3, 2)
                x, y, X, Y = getitem(rectangle1_domain, i, (0, 0, 999, 999))
                tmp[x:X + 1, y:Y + 1:Y - y] = 0, 0, 1
                tmp[x:X + 1:X - x, y:Y + 1] = 0, 0, 1
                y, x, Y, X = cv2.selectROI(wnd, tmp, printNotice=False)
                if not Y:
                    if i == len(rectangle1_domain):
                        break
                if Y:
                    setitem(rectangle1_domain, i, [x, y, x + X, y + Y])
                i += 1
            cv2.destroyAllWindows()
            key = ' '
            while True:
                wnd = f'{stage}{task}{_nok}/{_nng} {_okok}/{_ngok}'
                cv2.namedWindow(wnd)
                cv2.createTrackbar('i', wnd, 0, len(img) - 1, draw)
                cv2.createTrackbar('min', wnd, threshold[0], 255, draw)
                cv2.createTrackbar('max', wnd, threshold[1], 255, draw)
                cv2.createTrackbar('gamma', wnd, round(gamma + 50), 100, draw)
                key = chr(cv2.waitKey())
                i = cv2.getTrackbarPos('i', wnd)
                gamma = cv2.getTrackbarPos('gamma', wnd) - 50
                threshold = [cv2.getTrackbarPos('min', wnd), cv2.getTrackbarPos('max', wnd)]
                cv2.destroyAllWindows()
                if key in 'cr':
                    break
                if key == 'q':
                    exit()
                if key == 'd':
                    print('rm', file[i])
                    os.remove(file[i])
                    if i < _nok:
                        file[i] = file[_nok - 1]
                        img[i] = img[_nok - 1]
                        i = _nok - 1
                        _nok -= 1
                    else:
                        _nng -= 1
                    file[i] = file[-1]
                    img[i] = img[-1]
                    file.pop()
                    img = img[:-1]
                elif key == 'x':
                    print('mv', file[i])
                    tmp = file[i].replace(*'/OK/ /NG/'.split()[::(i < _nok) * 2 - 1])
                    os.rename(file[i], tmp)
                    if i < _nok:
                        file[i], file[_nok - 1] = file[_nok - 1], tmp
                        img[[i, _nok - 1]] = img[[_nok - 1, i]]
                        _nok -= 1
                        _nng += 1
                    else:
                        file[i], file[_nok] = file[_nok], tmp
                        img[[i, _nok]] = img[[_nok, i]]
                        _nok += 1
                        _nng -= 1
                elif key == 'o':
                    os.system(f'xdg-open {file[i]}')
                calcbox()
            if key == 'c':
                break
        cfg = {i: eval(i) for i in 'rectangle1_domain,threshold,_nok,_nng,_okok,_ngok'.split(',')}
        calcbase()
        cfg |= {f'{i}_base': j for i, j in zip(featids, base.tolist())}
        cfg |= zip(featids, (box - base).T.tolist())
        cfg = yaml.dump_all([cfg], Dumper=FlowDumper, sort_keys=False)
        open(f'{stage}.{task}.yml', 'w').write(cfg)
