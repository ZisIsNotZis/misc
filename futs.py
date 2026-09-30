from asyncio import Future, Task, CancelledError
from typing import AsyncIterator, Callable, Unpack
from weakref import WeakValueDictionary


def fut[T](s: T | BaseException | Future[T]) -> Future[T]:
    if not isinstance(s, Future):
        _ = Future()
        if isinstance(s, Exception):
            _.set_exception(s)
        else:
            _.set_result(s)
        s = _
    return s


def get[T](s: list[T], _: int, d: T = None) -> T:
    if -len(s) <= _ < len(s):
        return s[_]
    return d


def pop[T](s: list[T], _: int, d: Callable[[], T] = lambda: None) -> T:
    if -len(s) <= _ < len(s):
        return s.pop(_)
    return d()


def futpush[T](s: list[T], _: T) -> None:
    if isinstance(get(s, -1), BaseException):
        if isinstance(_, BaseException):
            return
        raise CancelledError
    if isinstance(get(s, -1), Future):
        if isinstance(s[-1], Exception):
            s.pop(-1).set_exception(_)
        else:
            s.pop(-1).set_result(_)
            return
    s.append(_)


def futpop[T](s: list[T]) -> Future[T]:
    return fut(s[0] if isinstance(get(s, 0), (BaseException, Future)) else pop(s, 0, lambda: s.append(_ := Future()) or _))


async def futpushes[T](s: list[T], _: AsyncIterator[T]) -> None:
    try:
        async for _ in _:
            futpush(s, _)
        raise StopAsyncIteration
    except Exception as _:
        futpush(s, _)


class Fut[T]:
    _: list[T]

    def __init__(self, *_: AsyncIterator[T]):
        self._ = []
        for _ in _:
            Task(futpushes(self._, _))

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    def __anext__(self) -> Future[T]:
        return futpop(self._)

    def __del__(self) -> None:
        futpush(self._, CancelledError())


class Cache[**P, T](WeakValueDictionary):
    def __init__(self, _: Callable[P, T]):
        super().__init__()
        self._ = _

    def __call__(self, *_: *P.args, **__: Unpack[P.kwargs]) -> T:
        if (___ := self.get(_)) is None:
            self[_] = ___ = self._(*_, **__)
        return ___
