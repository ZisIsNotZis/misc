from asyncio import sleep, Task, CancelledError
from dataclasses import dataclass
from functools import partial
from traceback import print_exc
import typing
from typing import Callable, Coroutine, Any

import numpy as np


class Sub(BaseException):
    pass


class Unsub(BaseException):
    pass


class Val[T]:
    def add(self, f: Callable[[T], Any]) -> None:
        raise NotImplementedError

    def remove(self, f: Callable[[T], Any]) -> None:
        raise NotImplementedError

    def __call__(self) -> T:
        raise NotImplementedError


@dataclass
class Val[T](set[Callable[[T], Any]]):
    arg: T | None = None
    f: Callable[[], T] | None = None
    sub: Callable[[], Any] = lambda: None
    unsub: Callable[[], Any] = lambda: None

    def add(s, f: Callable[[T], Any]) -> None:
        if not s:
            s.sub()
        super().add(f)

    def remove(self, f: Callable[[T], Any]) -> None:
        try:
            super().remove(f)
            if not self:
                self.unsub()
        except ValueError:
            pass

    def set(self, arg: T) -> None:
        self.arg = arg
        for i in tuple(self):
            try:
                i(arg)
            except Unsub:
                self.remove(i)
            except Exception:
                print_exc()

    def __call__(selfs):

    def __call__(self, arg: T) -> T:
        for i in self:
            try:
                i(arg)
            except Exception:
                print_exc()
        return arg


class Call[T]:
    def __call__(self) -> T | None:
        return None


class Fn[**P, T](Call[T]):
    f: Callable[P, T | None]

    def __init__(self, f: Callable[P, T], *arg: P.args, **kwarg: P.kwargs):
        self.f = f
        self.arg = arg
        self.kwarg = kwarg

    def __call__(self) -> T | None:
        return self.f(*self.arg, **self.kwarg)


type Lift[T] = T | Call[T] | Cb[T]


def lifted[**P, T](f: Callable[P, T]) -> Callable[P, Lift[T]]:
    def lifted(*arg: P.args, **kwarg: P.kwargs) -> Lift[T]:
        supcb: Cb | None = next((i for i in arg if isinstance(i, Cb)), None)

        def lifted(J=None) -> T:
            try:
                _: T = f(*[J if j == supcb else j() if isinstance(j, Call) else j for i, j in enumerate(arg)], **kwarg)  # type: ignore
                if _ is not None:
                    return cb(_)
            except Sub:
                if supcb is not None:
                    supcb.add(lifted)
            except Unsub:
                if supcb is not None:
                    supcb.remove(lifted)
            raise CancelledError

        if supcb is None:
            cb = Cb[T]()
        else:
            cb = supcb.mapped(lifted)
        return cb if any(isinstance(j, Cb) for j in arg) else Fn(lifted) if any(isinstance(j, Call) for j in arg) else lifted()

    return lifted


def unlift[T](arg: Lift[T]) -> T:
    return typing.cast(T, arg)


class Var[T](Call[T]):
    arg: T | None = None

    def __init__(self, arg: T | None = None):
        if arg is not None:
            lifted(self.set)(arg)

    def set(self, arg: T) -> None:
        self.arg = arg

    def __call__(self) -> T:
        if self.arg is None:
            raise CancelledError
        return self.arg


@Cb.sourced
async def Cam(cb: Cb[np.ndarray]) -> None:
    while True:
        await sleep(1)
        cb(np.empty((100, 100), 'B'))


@lifted
def VCam(img: np.ndarray, roi: tuple[slice]):
    return img[roi]


@Cb.sourced
async def Plc(cb: Cb[dict[int, int]] = Cb()) -> None:
    while True:
        await sleep(1)
        cb({1: 2, 3: 4})


@lifted
def Sig(plc: Lift[dict[int, int]], cfg: dict[tuple[int, int], str]) -> frozenset[str]:
    return frozenset({cfg[i] for i in unlift(plc).items() if i in cfg})


@lifted
def State(sig: Lift[frozenset[str]], cfg: dict[frozenset[str], str]) -> str | None:
    return cfg.get(unlift(sig))


State(Sig(Plc(), {(1, 2): '12', (3, 4): '34'}), {frozenset({'12'}): 'a', frozenset({'34'}): 'b'}).add(print)
