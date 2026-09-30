import asyncio.subprocess
import traceback
import typing


class Sub(Exception):
    pass


class Unsub(Exception):
    pass


class Cb[T](set[typing.Callable[[], None]]):
    def __init__(self, sub: typing.Callable[[], object] = lambda: None, unsub: typing.Callable[[], object] = lambda: None):
        super().__init__()
        self.sub = sub
        self.unsub = unsub
        self._: T | Exception = StopIteration()

    def add(self, f: typing.Callable[[], None]) -> None:
        if not self:
            try:
                self.sub()
            except Exception:
                traceback.print_exc()
        self.add(f)

    def remove(self, f: typing.Callable[[], None]) -> None:
        try:
            self.remove(f)
            if not self:
                try:
                    self.unsub()
                except Exception:
                    traceback.print_exc()
        except ValueError:
            pass

    def set(self, _: T | Exception | None | asyncio.Future[T | Exception | None]) -> None:
        if isinstance(_, asyncio.Future):
            _.add_done_callback(lambda _: self.set(_.result()))
        elif _ is not None and any_(_ != self._):
            self._ = _
            for f in self:
                try:
                    f()
                except Exception:
                    traceback.print_exc()

    def __call__(self) -> T | Exception:
        return self._


def callbacked[T](f: typing.Callable[[typing.Callable[[T | Exception | None], None]], typing.Callable[[], object]]) -> Cb[T]:
    cb = Cb[T](lambda: setattr(cb, 'unsub', f(cb.set)))
    return cb


def itered[T](f: typing.Callable[[], typing.AsyncGenerator[T | Exception | None]]) -> Cb[T]:
    @callbacked
    def _(cb: typing.Callable[[T | Exception | None], None]) -> typing.Callable[[], object]:
        async def _():
            try:
                async for _ in f():
                    cb(_)
            except Exception as _:
                cb(_)
            else:
                cb(StopIteration())

        job = asyncio.Task(_())
        return job.cancel

    return _


def mapped[**P, T](f: typing.Callable[P, T | Exception | None | asyncio.Future[T | Exception | None]]) -> typing.Callable[P, Cb[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Cb[T]:
        def g() -> None:
            try:
                cb.set(f(*[i() if isinstance(i, Cb) else i for i in arg], **{i: j() if isinstance(j, Cb) else j for i, j in kwarg.items()}))  # type: ignore
            except Sub:
                sub()
            except Unsub as _:
                unsub(*_.args)
            except Exception as _:
                cb.set(_)

        def sub() -> None:
            for ii in arg, kwarg.values():
                for i in ii:
                    if isinstance(i, Cb):
                        i.add(g)

        def unsub(*I) -> None:
            for ij in enumerate(arg), kwarg.items():
                for i, j in ij:
                    if (not I or i in I) and isinstance(j, Cb):
                        j.remove(g)

        cb = Cb[T](sub, unsub)
        return cb

    return _


def Proc(cmd: str, i: bool = False, o: bool = False) -> asyncio.Task[asyncio.subprocess.Process]:
    task = asyncio.Task(asyncio.create_subprocess_exec(*cmd.split(), stdin=-1 if i else None, stdout=-1 if o else None))
    task.add_done_callback(lambda done: print(cmd, done.exception() or done.result().pid))
    return task


def any_(o: object) -> bool:
    return bool(o.any() if hasattr(o, 'any') else o)
