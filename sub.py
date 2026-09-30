from typing import Callable, AsyncGenerator, Any
from asyncio import Task, CancelledError
from traceback import print_exc


class Unsub(Exception):
    pass


class Sub(Exception):
    pass


class Val[T]:
    o: T | None
    f: Callable[[], T | None] | None
    onsub: Callable[[], Any]
    onunsub: Callable[[], Any]
    onup: set[Callable[[], Any]]

    def __init__(self, o: T | None = None, f: Callable[[], T | None] | None = None, onsub: Callable[[], Any] = lambda: None, onunsub: Callable[[], Any] = lambda: None):
        self.o = o
        self.f = f
        self.onsub = onsub
        self.onunsub = onunsub
        self.onup = set()

    def set(self, o: T | None) -> None:
        if o is not None and not eq(o, self.o):
            self.o = o
            for i in list(self.onup):
                try:
                    i()
                except CancelledError:
                    pass
                except Exception:
                    print_exc()

    def __call__(self) -> T:
        if self.f:
            self.set(self.f())
        if self.o is None:
            raise CancelledError
        return self.o

    def sub(self, f: Callable[[], Any]) -> None:
        if not self.onup:
            self.onsub()
        self.onup.add(f)

    def unsub(self, f: Callable[[], Any]) -> None:
        try:
            self.onup.remove(f)
            if not self.onup:
                self.onunsub()
        except ValueError:
            pass

    def __str__(self) -> str:
        return f'Var({self.f if self.f else self.o})'

    def __repr__(self) -> str:
        return str(self)


type ValLike[T] = T | Val[T]


def eq(a: Any, b: Any) -> bool:
    try:
        o = a == b
        if hasattr(o, 'all'):
            return o.all()
        return o
    except ValueError:
        return False


def sourced[**P, T](f: Callable[P, AsyncGenerator[T, None]]) -> Callable[P, Val[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Val[T]:
        job: Task[None] | None = None

        def onsub() -> None:
            nonlocal job

            @lambda _: Task(_())
            async def _() -> None:
                print(f, *arg, 'beg')
                try:
                    async for i in f(*arg, **kwarg):
                        print(f, *arg, i)
                        val.set(i)
                finally:
                    print(f, *arg, 'end')

            job = _

        def onunsub() -> None:
            if job:
                job.cancel()

        val = Val[T](onsub=onsub, onunsub=onunsub)
        return val

    return _


def lifted[**P, T](f: Callable[P, T]) -> Callable[P, Val[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Val[T]:
        def _() -> T | None:
            try:
                o = f(*[i() if isinstance(i, Val) else i for i in arg], **{i: j() if isinstance(j, Val) else j for i, j in kwarg.items()})  # type: ignore
                print(f, *arg, o)
                return o
            except Sub:
                onsub()
            except Unsub as e:
                onunsub(*e.args)
            return None

        def onsub() -> None:
            for jj in arg, kwarg.values():
                for j in jj:
                    if isinstance(j, Val):
                        j.sub(val)

        def onunsub(*I: int | str) -> None:
            for ij in enumerate(arg), kwarg.items():
                for i, j in ij:
                    if (not I or i in I) and isinstance(j, Val):
                        j.unsub(val)

        val = Val[T](f=_, onsub=onsub, onunsub=onunsub)
        return val

    return _


def unlift[T](o: ValLike[T]) -> T:
    assert not isinstance(o, Val)
    return o
