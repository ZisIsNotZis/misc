# Import required modules
from itertools import zip_longest
from typing import overload, Iterable

from fastapi import FastAPI, Body, Response
import numpy as np
import builtins

# Initialize FastAPI app
api = FastAPI()


@overload
def zip[A, B](*a: tuple[A, B]) -> tuple[tuple[A, ...], tuple[B, ...]]: ...
@overload
def zip[A, B](a: Iterable[A], b: Iterable[B]) -> tuple[tuple[A, B], ...]: ...


def zip(*a):
    """
    Overloaded zip function for type hinting. Uses built-in zip.
    """
    return builtins.zip(*a)


def fromarrays(a: tuple[np.ndarray, ...], name: tuple[str, ...]) -> np.ndarray:
    """
    Combines multiple numpy arrays into a structured array with named fields.
    Args:
        a: Tuple of numpy arrays.
        name: Tuple of field names.
    Returns:
        Structured numpy array.
    """
    if len(a) < 2:
        return a[0].view([(name[0], a[0].dtype)])
    # Find the dimension where shapes differ
    dim = min(next(i for i, (j, k) in enumerate(zip_longest(a[0].shape, b.shape + (0,))) if j != k) for b in a[1:])
    # Create output structured array
    out = np.empty(a[0].shape[:dim], [(i, j.dtype, j.shape[dim:]) for i, j in zip(name, a)])
    for i, j in zip(name, a):
        out[i] = j
    return out


def unpackbits(a: np.ndarray) -> np.ndarray:
    """
    Recursively unpacks bits from a numpy array, handling structured arrays.
    Args:
        a: Numpy array to unpack.
    Returns:
        Unpacked numpy array.
    """
    if a.dtype.base == "B":
        return np.unpackbits(a, -1).view("?")
    # Recursively unpack fields if structured
    sub, change = zip(*[(t, t is not a[i]) for i in a.dtype.names for t in [unpackbits(a[i])]])
    if a.dtype.names and any(change):
        return fromarrays(sub, a.dtype.names)
    return a


def packbits(a: np.ndarray) -> np.ndarray:
    """
    Recursively packs bits into a numpy array, handling structured arrays.
    Args:
        a: Numpy array to pack.
    Returns:
        Packed numpy array.
    """
    if a.dtype.names and a.dtype[0] == "?":
        return np.packbits(a[..., None].view("?"), -1)
    # Recursively pack fields if structured
    sub, change = zip(*[(t, t is not a[i]) for i in a.dtype.names for t in [packbits(a[i])]])
    if a.dtype.names and any(change):
        return fromarrays(sub, a.dtype.names)
    return a


def tobj(a: np.ndarray) -> dict | list:
    """
    Converts a numpy array to a Python object (list or dict), handling structured arrays.
    Args:
        a: Numpy array.
    Returns:
        Python list or dict representation.
    """
    return a.tolist() if not a.dtype.names else [tobj(a) for a in a] if a.ndim else {i: tobj(a[i]) for i in a.dtype.names}


# def fromobj(a: dict | list, type, d=0) -> tuple | list:
#     """
#     Converts a Python object (dict or list) to a tuple or list suitable for numpy structured arrays.
#     Args:
#         a: Python object (dict or list).
#         type: Numpy dtype.
#         d: Default value.
#     Returns:
#         Tuple or list for numpy array construction.
#     """
#     return [fromobj(a, type, d) for a in a] if isinstance(a, list) else tuple(fromobj(a[i], type, d) if i in a else d for i, (type, _) in type.fields.items()) if isinstance(a, dict) else a


def fromobj(a: dict | list, type, d=0) -> tuple | list:
    """
    Converts a Python object (dict or list) to a tuple or list suitable for numpy structured arrays.
    Args:
        a: Python object (dict or list).
        type: Numpy dtype.
        d: Default value.
    Returns:
        Tuple or list for numpy array construction.
    """
    return [fromobj(a[min(i, len(a)-1)], np.dtype((type.base, type.shape[1:])), d) for i in range(type.shape[0]if type.shape else len(a))] if isinstance(a, list) else tuple(fromobj(a[i], type, d) if i in a else d for i, (type, _) in type.fields.items()) if isinstance(a, dict) else a


@api.post("/tobytes")
def tobytes(a: dict | list, type: str) -> Response:
    """
    FastAPI endpoint to convert a Python object to packed bytes using numpy structured arrays.
    Args:
        a: Python object (dict or list).
        type: String representation of numpy dtype.
    Returns:
        Response containing packed bytes.
    """
    type = eval(type)
    return Response(packbits(np.array(fromobj(a, np.dtype(type)), type)).tobytes(), media_type="application/octet-stream")


@api.post("/frombytes")
def frombytes(type: str, compactype: str = None, a: bytes = Body(...)) -> dict | list:
    """
    FastAPI endpoint to convert bytes to a Python object using numpy structured arrays.
    Args:
        type: String representation of numpy dtype.
        compactype: Optional string representation of compact dtype for unpacking bits.
        a: Bytes input.
    Returns:
        Python object (dict or list).
    """
    return tobj(np.frombuffer(unpackbits(np.frombuffer(a, eval(compactype))) if compactype else a, eval(type)))
