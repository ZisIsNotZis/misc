import numpy as np


def feat2(a: np.ndarray):
    a = a / a.sum((-2, -1), 'f', keepdims=True)
    a1 = a.sum(-2, keepdims=True)
    a2 = a.sum(-1, keepdims=True)
    x = np.linspace(0, 1, a.shape[-2], dtype='f')[:, None]
    y = np.linspace(0, 1, a.shape[-1], dtype='f')[None]
    m10 = a2.mT @ x
    m01 = a1 @ y.mT
    x = x - m10
    y = y - m01
    m11 = (x * y).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    x2 = x ** 2
    y2 = y ** 2
    r = (x2 + y2).reshape(*a.shape[:-2], 1, -1) ** .5 @ a.reshape(*a.shape[:-2], -1, 1)
    m20 = a2.mT @ x2
    m02 = a1 @ y2.mT
    m20_02 = m20 - m02
    h1 = m20 + m02
    h2 = m20_02 ** 2 + 4 * m11
    h8 = m20 * m11 * m02
    aspect = m20 / m02
    area = m20 * m02
    cov = m11 / area ** .5
    phi = m11 / (m20_02 + 1e-9)
    det = m02 * m20 - m11 * m11
    discr = (h1 ** 2 / 4 - det) ** .5
    ia = h1 / 2 + discr
    ib = h1 / 2 - discr
    rotaspect = ia / ib
    rotarea = ia * ib
    return locals()


def feat3(a: np.ndarray):
    _ = feat2(a)
    a, a1, a2, x, y, x2, y2, m20, m11, m02, m20_02 = [_[a] for a in 'a,a1,a2,x,y,x2,y2,m20,m11,m02,m20_02'.split(',')]
    m21 = (x2 * y).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    m12 = (x * y2).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    x3 = x2 * x
    y3 = y2 * y
    m30 = a2.mT @ x3
    m03 = a1 @ y3.mT
    m3012 = m30 + m12
    m2103 = m21 + m03
    m30_12 = m30 - 3 * m12
    m21_03 = 3 * m21 - m03
    m30122 = m3012 ** 2
    m21032 = m2103 ** 2
    m3012_ = m3012 * (m30122 - 3 * m21032)
    m2103_ = m2103 * (3 * m30122 - m21032)
    h3 = m30_12 ** 2 + m21_03 ** 2
    h4 = m30122 + m21032
    h5 = m30_12 * m3012_ + m21_03 * m2103_
    h6 = m20_02 * (m30122 - m21032) + 4 * m11 * m3012 * m2103
    h7 = m21_03 * m3012_ - m30_12 * m2103_
    h9 = m3012 - m2103
    m30_ = m30 / m20 ** 1.5
    m03_ = m03 / m02 ** 1.5
    return _ | {a: _ for a, _ in locals().items() if a != '_'}


def feat4(a: np.ndarray):
    _ = feat3(a)
    a, a1, a2, x, y, x2, y2, x3, y3, m20, m02 = [_[a] for a in 'a,a1,a2,x,y,x2,y2,x3,y3,m20,m02'.split(',')]
    m31 = (x3 * y).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    m22 = (x2 * y2).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    m13 = (x * y3).reshape(*a.shape[:-2], 1, -1) @ a.reshape(*a.shape[:-2], -1, 1)
    x4 = x3 * x
    y4 = y3 * y
    m40 = a2.mT @ x4
    m04 = a1 @ y4.mT
    m40_ = m40 / m20 ** 2
    m04_ = m04 / m02 ** 2
    return _ | {a: _ for a, _ in locals().items() if a != '_'}


def featc(a: np.ndarray):
    a = a / a.mean((-2, -1), 'f', keepdims=1)
    std = a.std((-2, -1), keepdims=1)
    skew = np.cbrt(((a - 1 / a.size) ** 3).mean((-2, -1), keepdims=1))
    kurtosis = ((a - 1 / a.size) ** 4).sum((-2, -1), keepdims=1) ** .25
    i, j, k, l = np.percentile(a, [.2, .4, .6, .8], axis=(-2, -1), keepdims=1)
    return locals()


def feat(a: np.ndarray):
    return {f'{a}.': _.ravel() if _.size > 1 else _.item() for a, _ in feat3(a).items() if _.shape[-2:] == (1, 1)} | {f'{a}_': _.ravel() if _.size > 1 else _.item() for a, _ in featc(a).items() if _.shape[-2:] == (1, 1)}
