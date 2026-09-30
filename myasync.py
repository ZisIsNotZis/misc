from asyncio import CancelledError
from time import time, sleep
from typing import Callable

STACK: list['Task'] = []
NEW: list['Task'] = []
OLD: list['Task'] = []
DEF: list['Task'] = []
SLEEP: list['Sleep'] = []


class Fut[T]:
    o: T | Exception | ...
    arg: tuple
    kwarg: dict[str, ...]
    old: list['Task']

    def __init__(self, o: T | Exception | ... = ..., *arg, **kwarg):
        self.o = o
        self.arg = arg
        self.kwarg = kwarg
        self.old = []

    def __call__(self, o: T | Exception | ... = ...) -> T | None:
        if o is not ...:
            self.o = o
            OLD[:] += self.old
            del self.old[:]
            return
        if not self:
            self.old += STACK[-1:]
            self.o = CancelledError()
            Loop()
        if isinstance(self.o, Exception):
            raise self.o
        return self.o

    def __bool__(self):
        return self.o is not ...

    def __repr__(self):
        return f'{type(self).__name__}({self.o}{"".join(f",{i}" for i in self.arg)}{"".join(f",{i}={j}" for i, j in self.kwarg.items())})'


class Sleep(Fut[None]):
    def __init__(self, arg: float):
        super().__init__(..., time() + arg)
        SLEEP[:] += self,


class Task[T](Fut[T]):
    def __init__(self, f: Callable[..., T], *arg, **kwarg):
        super().__init__(..., f, *arg, **kwarg)
        NEW[:] += self,

    def __call__(self, o: T | Exception | ... = ...) -> T | None:
        if o is ... and not self:
            try:
                super().__call__(self.arg[0](*self.arg[1:], **self.kwarg))
            except Exception as o:
                super().__call__(o)
        return super().__call__()


def Async[T:Callable](f: T) -> T:
    def _(*arg, **kwarg):
        return Task(f, *arg, **kwarg)

    return _


def Loop():
    while STACK or NEW or SLEEP:
        SLEEP[:] = [i for i in SLEEP if i.arg[0] > time() or i(None)]
        if STACK and STACK[-1] in OLD:
            return
        elif NEW:
            STACK[:] += NEW.pop(),
            try:
                STACK[-1]()
                NEW[:0] += DEF
                del DEF[:]
            except CancelledError:
                DEF[:] += (_ := STACK[-1]),
            finally:
                try:
                    OLD.remove(STACK[-1])
                except ValueError:
                    pass
                del STACK[-1]
        elif SLEEP:
            sleep(min(i.arg[0] for i in SLEEP) - time())
        elif STACK:
            raise CancelledError


class Q[T](list[Fut[T]]):
    def __call__(self, o: T | Exception):
        if self and not self[-1]:
            self.pop()(o)
        self[:] += Fut(o),

    def __iter__(self):
        return self

    def __next__(self) -> T:
        if self:
            return self.pop(0)()
        self[:] += (_ := Fut()),
        return _()
