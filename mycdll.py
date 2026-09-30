import ctypes
import os

import numpy as np


def CDLL(name: str):
    def CDLL(f):
        g = getattr(ctypes.CDLL(name), f.__name__)
        g.argtypes = [f.__annotations__.get(i, ctypes.c_int) for i in f.__code__.co_varnames[:f.__code__.co_argcount]]
        g.restype = f.__annotations__.get('return', ctypes.c_int)
        return g

    return CDLL


@CDLL('libc.so.6')
def mmap(ptr: ctypes.c_long, length: ctypes.c_long, flag, prot, fd, offset: ctypes.c_long) -> ctypes.c_long: ...


def fromfile(f: str) -> np.ndarray:
    return np.fromfile(f, f.split('.')[-1])[0]


def memmap(f: str, creat=False) -> np.ndarray:
    t = np.dtype(f.split('.')[-1])
    f = os.open(f, os.O_RDWR | creat * os.O_CREAT)
    os.ftruncate(f, t.itemsize)
    m = mmap(0, t.itemsize, 0x3, 0x01, f, 0)
    os.close(f)
    return np.frombuffer((ctypes.c_char * t.itemsize).from_address(m), t)[0]


def chunk(a: list, n=4):
    for i in range(0, len(a), n):
        yield a[i:i + n]


def vcache(f):
    def _(*args, _={}, **kwargs) -> list:
        for i in chunk([i for i in args if i not in _]):
            for i, j in zip(i, f(*i, **kwargs)):
                if j is not None:
                    _[i] = j
        return [_.get(i) for i in args]

    return _
