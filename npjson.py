import numpy as np
import itertools

type Json = dict[str, Json] | list[Json] | float | str | None


def dump(a: np.ndarray) -> Json:
    return a.tolist()if not a.dtype.names else list(map(dump, a)) if a.ndim else {i: dump(a[i])for i in a.dtype.names}


def load(a: np.ndarray, b: Json):
    if b is not None:
        try:
            B = np.array(b, a.dtype)
        except TypeError:
            if a.ndim and isinstance(b, (dict, list)):
                [load(a[i:i+1].squeeze(0), b[i]if isinstance(b, list)else b)for i in range(min(len(b), len(a))if isinstance(b, list)else len(a))]
            elif a.dtype.names and isinstance(b, (dict, list)):
                [load(a[i], b[i]if isinstance(b, dict)else b)for i in (set(b).intersection(a.dtype.names) if isinstance(b, dict)else a.dtype.names)]
            else:
                print(a, b)
                raise
        else:
            a[*(slice(min(a, b))for a, b in zip(a.shape, B.shape))] = B[*(slice(min(a, b))for a, b in zip(a.shape, B.shape)), *(None,)*(a.ndim-B.ndim)]


def dumpdiff(a: np.ndarray, b: np.ndarray, m: np.ndarray | None = None) -> Json:
    M = a != b if m is None else m
    if not M.any():
        return None
    if M.ndim:
        _ = list(itertools.starmap(dumpdiff, zip(a, b, M)))
        return _[0]if all(i == _[0]for i in _) else list(itertools.dropwhile(lambda _: _ is None, _[::-1]))[::-1]
    if a.dtype.names:
        _ = {i: dumpdiff(a[i], b[i])for i in a.dtype.names}
        __ = next(iter(_.values()))
        return __ if all(type(_) == type(__) and _ == __ for _ in _.values()) else {i: _ for i, _ in _.items()if _ is not None}
    return b


a = np.empty((3, 4), 'f,2i')
print(a)
b = np.empty_like(a)
print(b)
diff = dumpdiff(a, b)
print(diff)
load(a, diff)
print(a == b)
