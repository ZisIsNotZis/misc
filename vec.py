import numpy as np


class Vec(np.ndarray):
    def __new__(s, file, dtype='f', len=0):
        if isinstance(file, str):
            try:
                file = np.memmap(file, dtype)
                len = file.shape[0]
                file = file._mmap
            except FileNotFoundError:
                file = np.memmap(file, dtype, 'w+', shape=len)._mmap
                len = 0
        s = np.ndarray.__new__(Vec, file.size()//np.dtype(dtype).itemsize, dtype, file)
        s.file = file
        s.len = len
        return s

    def append(s, dat):
        if not hasattr(dat, '__iter__'):
            dat = dat,
        if s.len + len(dat) > len(s):
            s.file.resize((s.len+len(dat))*2*s.itemsize)
            s = Vec(s.file, s.dtype, s.len)
        s[s.len:s.len+len(dat)] = dat
        s.len += len(dat)
        return s

    def trunc(s):
        file = s.file
        s = s[:s.len]
        s.file = file
        s.len = len(s)
        return s
