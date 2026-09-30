from asyncio import Task, Future, ensure_future
from typing import Coroutine, Callable, Any, Awaitable


def set_result[T](a: Callable[[], T], b: Future[T]) -> None:
    try:
        b.set_result(a())
    except BaseException as _:
        b.set_exception(_)


def set_exception(a: Callable[[], object], b: Future[object]) -> None:
    try:
        a()
    except BaseException as _:
        b.set_exception(_)


def connect_result[T, U](a: Awaitable[T], b: Future[U] | None = None, f: Callable[[T], U] = lambda _: _) -> Future[U]:
    A = ensure_future(a)
    b = b or Future()
    b.add_done_callback(lambda b: b.cancelled() and A.cancel())
    A.add_done_callback(lambda a: set_result(lambda: f(a.result()), b))
    return b


def connect_exception[T](a: Awaitable[T], b: Future[object] | None = None, f: Callable[[T], object] = lambda: None):
    A = ensure_future(a)
    b = b or Future()
    b.add_done_callback(lambda b: b.cancelled() and A.cancel())
    A.add_done_callback(lambda a: set_exception(lambda: f(a.result()), b))
    return b


def map_future[T, U](a: Awaitable[T], f: Callable[[T], U]) -> Future[U]:
    return connect_result(a, None, f)


def flatmap_future[T, U](a: Awaitable[T], f: Callable[[T], Awaitable[U]]) -> Future[U]:
    b = Future[U]()
    return connect_exception(a, b, lambda A: connect_result(f(A), b))


def mapcoro2[T, U](a: Coroutine[Any, Any, T], f: Callable[[T], Coroutine[Any, Any, U]]) -> Future[U]:
    fu = Future()

    @Task(a).add_done_callback
    def _(ta: Task[Coroutine[Any, Any, T]]):
        try:
            @Task(f(ta.result())).add_done_callback
            def _(tb: Task[Coroutine[Any, Any, U]]):
                try:
                    fu.set_result(tb.result())
                except Exception as e:
                    fu.set_exception(e)
        except Exception as e:
            fu.set_exception(e)

    return fu
