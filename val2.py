import asyncio.subprocess
import base64
import io
import sys
import time
import traceback
from typing import *

import PIL.Image
import numpy as np
import pydantic


def any_(_: bool) -> bool:
    return _.any() if hasattr(_, 'any') else _


class Sub(Exception):
    pass


class Unsub(Exception):
    pass


class Cb[T](set[Callable[[T], object]]):
    def __init__(self, sub: Callable[[], None] = lambda: None, unsub: Callable[[], None] = lambda: None):
        super().__init__()
        self.sub = sub
        self.unsub = unsub

    def add(self, f: Callable[[T], None]) -> None:
        if not self:
            self.sub()
        self.add(f)

    def unsub(self, f: Callable[[T], None]) -> None:
        try:
            self.remove(f)
            if not self:
                self.unsub()
        except ValueError:
            pass

    def __call__(self, o: T) -> None:
        for f in self:
            _ = f(o)
            if isinstance(_, Coroutine):
                asyncio.Task(_)


def cbsrc[**P, T](f: Callable[P, AsyncGenerator[T]]) -> Callable[P, Cb[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Cb[T]:
        job: asyncio.Task[None] | None = None

        def sub():
            nonlocal job

            @lambda _: asyncio.Task(_())
            async def job():
                async for _ in f(*arg, **kwarg):
                    cb(_)

        def unsub():
            job.cancel()

        cb = Cb[T](sub=sub, unsub=unsub)
        return cb

    return _


def cblift[**P, T, U](f: Callable[P, Generator[T, U]]) -> Callable[P, Callable[[Cb[U]], Cb[T]]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Callable[[Cb[U]], Cb[T]]:
        def _(src: Cb[U]) -> Cb[T]:
            g: Generator[T, U] | None = None

            def sub():
                nonlocal g
                g = f(*arg, **kwarg)
                g.send(None)
                src.add(g.send)

            def unsub():
                src.remove(g.send)
                g.close()

            cb = Cb[T](sub=sub, unsub=unsub)
            return cb

        return _

    return _


def cbmap[T, U](f: Callable[[U], T]) -> Callable[[Cb[U]], Cb[T]]:
    def _(src: Cb[U]) -> Cb[T]:
        def g(o: U):
            cb(f(o))

        def sub():
            src.add(g)

        def unsub():
            src.remove(g)

        cb = Cb[T](sub=sub, unsub=unsub)
        return cb

    return _


class Val[T]:
    def __init__(self, v: T | Exception = AssertionError(), t: float = 0., f: Callable[[], T | None] = lambda: None, ft: Callable[[], float] = lambda: time.time(), onsub: Iterable[Callable[..., object]] = (), onunsub: Iterable[Callable[..., object]] = (), onup: Iterable[Callable[..., object]] = ()):
        self.v = v
        self.t = t
        self.f = f
        self.ft = ft
        self.onsub = set(onsub)
        self.onunsub = set(onunsub)
        self.onup = set(onup)

    def sub(self, f: Callable[..., object], *msg) -> None:
        if not self.onup:
            for i in tuple(self.onsub):
                try:
                    i(*msg)
                except Exception:
                    traceback.print_exc()
        self.onup.add(f)

    def unsub(self, f: Callable[[], object], *msg) -> None:
        try:
            self.onup.remove(f)
            if not self.onup:
                for i in tuple(self.onunsub):
                    try:
                        i(*msg)
                    except Exception:
                        traceback.print_exc()
        except ValueError:
            pass

    def up(self, *msg) -> Self:
        if (t := self.ft()) > self.t:
            try:
                _ = self.f()
            except Exception as e:
                _ = e
            self(_, t, *msg)
        return self

    def __call__(self, v: T | Exception | None = None, t: float = 0., *msg, e: bool = True) -> T:
        if v is not None:
            if (t := t or time.time()) > self.t:
                self.t = t
                if v is not None and any_(v != self.v):
                    self.v = v
                    for i in tuple(self.onup):
                        try:
                            i(*msg)
                        except Exception:
                            traceback.print_exc()
        if e and isinstance(self.v, Exception):
            raise self.v
        return self.v


def itered[**P, T](f: Callable[P, AsyncGenerator[T]]) -> Callable[P, Val[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Val[T]:
        job: asyncio.Task[None] | None = None

        def sub():
            nonlocal job

            @lambda _: asyncio.Task(_())
            async def job():
                async for i in f(*arg, **kwarg):
                    val(i)

        def unsub():
            job.cancel()

        val = Val[T](onsub=[sub], onunsub=[unsub])
        return val

    return _


def lifted[**P, T](g: Callable[P, T]) -> Callable[P, Val[T]]:
    def _(*arg: P.args, **kwarg: P.kwargs) -> Val[T]:
        def f() -> T | None:
            try:
                return g(*[i.v if isinstance(i, Val) else i for i in arg], **{i: j.v if isinstance(j, Val) else j for i, j in kwarg.items()})  # type: ignore
            except Sub:
                sub()
            except Unsub as e:
                unsub(*e.args)

        def tf() -> float:
            return sum(j.up().t for i in (arg, kwarg.values()) for j in i if isinstance(j, Val))

        def sub() -> None:
            for i in (arg, kwarg.items()):
                for j in i:
                    if isinstance(j, Val):
                        j.sub(val.up)

        def unsub(*I) -> None:
            for ij in (enumerate(arg), kwarg.items()):
                for i, j in ij:
                    if (not I or i in I) and isinstance(j, Val):
                        j.unsub(val.up)

        val = Val[T](f=f, ft=tf, onsub=[sub], onunsub=[unsub])
        return val

    return _


type ValLike[T] = Val[T] | T


def unlift[T](v: ValLike[T]) -> T:
    assert not isinstance(v, Val)
    return v


class Enum(int):
    @staticmethod
    def __get_validators__():
        return lambda a, _: Enum(a),


class Image(np.ndarray):
    def __new__(cls, a: str | bytes | PIL.Image.Image | np.ndarray | IO):
        if isinstance(a, str):
            a = base64.b64decode(a)
        if isinstance(a, bytes):
            a = io.BytesIO(a)
        if isinstance(a, (IO, io.BytesIO)):
            a = PIL.Image.open(a)
        if isinstance(a, PIL.Image.Image):
            a = np.asarray(a)
        if a.ndim > 2:
            a = a.mean(-1, a.dtype)
        assert isinstance(a, np.ndarray)
        return a.view(cls)

    @staticmethod
    def __get_validators__():
        return lambda a, _: Image(a),


class TaskCfg(pydantic.BaseModel):
    rectangle1_domain: list[int | list[int]] = [0, 0, 540, 720]
    threshold: list[int] = [0, 128]
    connect: int = 0
    model_config = {"extra": "allow"}


class StageCfg(pydantic.BaseModel):
    if_: list[str] = pydantic.Field([], alias="if")
    time: float = 300.
    task: dict[str, TaskCfg] = {}
    model_config = {"extra": "forbid"}


class MissionCfg(pydantic.BaseModel):
    sig: dict[int | float, dict[int, str]] = {}
    stage: dict[str, StageCfg] = {}
    model_config = {"extra": "forbid"}


class NozzleCfg(pydantic.BaseModel):
    x: int = 0
    y: int = 0
    X: int = 9999
    Y: int = 9999
    tbr: int = 30
    transpose: bool = False
    preset: str = 'slow'
    q: int = 20
    mission: dict[str, MissionCfg]
    model_config = {"extra": "forbid"}


class CamCfg(pydantic.BaseModel):
    uri: str
    nozzle: dict[str, NozzleCfg] = pydantic.Field(alias="nozle")
    OffsetY: int = 0
    OffsetX: int = 0
    Height: int = 540
    Width: int = 720
    ReverseX: bool = False
    ReverseY: bool = False
    AcquisitionFrameRate: float = 30.
    AcquisitionFrameRateEnable: bool = True
    BinningHorizontal: Enum = pydantic.Field(Enum(1), alias="BinningHorizontal:Enum")
    BinningVertical: Enum = pydantic.Field(Enum(1), alias="BinningVertical:Enum")
    ExposureTime: float = 10000.
    TriggerMode: Enum = Enum(0)  # MV_TRIGGER_MODE_OFF
    orderFactor: float = 1.
    model_config = {"extra": "forbid"}


class AreaCfg(pydantic.BaseModel):
    sig: dict[int | float, dict[int, str]] = {}
    cam: dict[str, CamCfg]
    model_config = {"extra": "forbid"}


class UnitCfg(pydantic.BaseModel):
    area: dict[str, AreaCfg]
    model_config = {"extra": "forbid"}


class FloorCfg(pydantic.BaseModel):
    plc: str = ''
    unit: dict[str, UnitCfg]
    model_config = {"extra": "forbid"}


class Cfg(pydantic.BaseModel):
    cfg: dict[str, FloorCfg]
    model_config = {"extra": "forbid"}


def inf(*_) -> None:
    print(*_, file=sys.stderr)


def wrn(*_) -> None:
    s = ' '.join(map(str, _))
    print('wrn', s, file=sys.stderr)
    for i in XLOG:
        i('be/wrn', s)


def err(*_) -> None:
    s = ' '.join(map(str, _))
    print(s, file=sys.stderr)
    traceback.print_exc()
    for i in XLOG:
        i('be/err', s)


def elide(_: Any) -> str:
    s = str(_).replace('\n', '')
    return s if len(s) < 80 else s[:40] + s[40:]


def Proc(arg: str, i: bool = False, o: bool = False) -> asyncio.Task[asyncio.subprocess.Process]:
    task = asyncio.Task(asyncio.create_subprocess_exec(*arg.split(), stdin=-1 if i else None, stdout=-1 if o else None))
    task.add_done_callback(lambda done: (wrn if done.exception() else inf)(arg, done.exception() or done.result().pid))
    return task


XLOG: list[Callable[[str, object], None]] = []
