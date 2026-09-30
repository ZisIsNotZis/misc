#!/bin/env python
import sklearn
import sys
import os
import numpy as np
import cv2


def signpow(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.sign(a)*abs(a)**b


def feat(nhw: np.ndarray) -> dict[str, np.ndarray]:
    o = {}
    m00 = nhw.mean((1, 2))+1e-9
    # o['m00'] = m00
    nhw = np.divide(nhw, m00[:, None, None])
    nh = nhw.sum(2)
    nw = nhw.sum(1)
    I = np.linspace(0, 1, nh.shape[1], dtype=nhw.dtype)
    J = np.linspace(0, 1, nw.shape[1], dtype=nhw.dtype)
    o['m10'] = nh@I
    o['m01'] = nw@J
    # o['s'] = nhw.std((1, 2))
    # o['s0'] = nh.std(1)
    # o['s1'] = nw.std(1)
    y = I-o['m10'][:, None]
    x = J-o['m01'][:, None]
    # o['u10'] = np.einsum('nh,nh->n', nh, abs(y))
    # o['u01'] = np.einsum('nw,nw->n', nw, abs(x))
    o['u20'] = np.einsum('nh,nh->n', nh, y**2)
    # o['u11'] = np.einsum('nhw,nhw->n', nhw, y[:, :, None]*x[:, None])
    o['u02'] = np.einsum('nw,nw->n', nw, x**2)
    # o['u30'] = np.einsum('nh,nh->n', nh, y**3)
    # o['u21'] = np.einsum('nhw,nhw->n', nhw, y[:, :, None]**2*x[:, None])
    # o['u12'] = np.einsum('nhw,nhw->n', nhw, y[:, :, None]*x[:, None]**2)
    # o['u03'] = np.einsum('nw,nw->n', nw, x**3)
    # r = (y[:, :, None]**2+x[:, None]**2)
    # o['r1'] = np.einsum('nhw,nhw->n', nhw, r)
    # o['r3'] = np.einsum('nhw,nhw->n', nhw, r**3)
    return o


def pca(feat: dict[str, np.ndarray], q=.95) -> np.ndarray:
    pca = sklearn.decomposition.PCA(q)
    y = pca.fit_transform(sklearn.preprocessing.StandardScaler().fit_transform(np.stack(list(feat.values()), 1)))
    print(dict(map(reversed, sorted(zip(((_ := pca.explained_variance_@pca.components_**2)/_.sum()).tolist(), feat)))))
    return y


def clsmeanstd(a: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    c = c+1
    s = np.zeros((c.max()+1, *a.shape[1:]), a.dtype)
    np.add.at(s, c, a)
    s2 = np.zeros_like(s)
    np.add.at(s2, c, np.square(a))
    n = np.ones(len(s), 'H')
    np.add.at(n, c, 1)
    s /= n[:, *[None]*(a.ndim-1)]   
    s2 /= n[:, *[None]*(a.ndim-1)]
    s2 -= np.square(s)
    return s[1:], np.sqrt(s2, s2)[1:]


def normalize_(nhw: np.ndarray):
    nhw -= nhw.mean((1, 2), keepdims=1)
    ij = np.stack(np.broadcast_arrays(np.arange(nhw.shape[1], dtype=nhw.dtype)[:, None], np.arange(nhw.shape[2], dtype=nhw.dtype)), 2).reshape(-1, 2)
    ij -= ij.mean(0)
    np.linalg.lstsq(ij, nhw.reshape(len(nhw), -1).T)[0]
    nhw.reshape(len(nhw), -1)[:] -= np.linalg.lstsq(ij, nhw.reshape(len(nhw), -1).T)[0].T@ij.T
    nhw /= nhw.std((1, 2), keepdims=1)
    return nhw


def scaleminmax_(nhw: np.ndarray):
    nhw -= nhw.min((-2, -1), keepdims=1)
    nhw /= nhw.max((-2, -1), keepdims=1)+1e-9
    return nhw


nhw = normalize_(np.stack([cv2.imread(i, cv2.IMREAD_GRAYSCALE)for i in sys.argv[4:]]).astype('f'))
c = sklearn.cluster.KMeans(int(sys.argv[3])).fit_predict(pca(feat(scaleminmax_(normalize_(nhw[:, *(slice(*i)for i in np.array(cv2.selectROI(' '.join(sys.argv[1:4]+[os.getcwd()]), scaleminmax_(np.sqrt(nhw.std(0))))).reshape(2, 2).T[::-1].cumsum(1))])))))
for i, j in enumerate((scaleminmax_(np.sqrt(clsmeanstd(nhw, c)[1]))*255.9).astype('B')):
    os.makedirs(f'{sys.argv[2]}{i}', exist_ok=1)
    cv2.imwrite(f'{sys.argv[2]}{i}.jpg', j)
for i, j in zip(sys.argv[4:], c):
    if j >= 0:
        getattr(os, sys.argv[1])(f'{'../'*(sys.argv[1] == 'symlink' and sys.argv[2].count('/')+1)}{i}', f'{sys.argv[2]}{j}/{i}')
