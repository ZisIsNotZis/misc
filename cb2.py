from asyncio import Task
from dataclasses import dataclass
from traceback import print_exc
from typing import Callable, Any, Coroutine


class Unsub(BaseException):
    pass


@dataclass
class Val[T](set[Callable[[T], Any]]):
    arg: T | None = None
    f: Callable[[], T | None] = lambda: None
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

    def set(self, arg: T | None) -> None:
        if arg is not None and arg != self.arg:
            self.arg = arg
            for i in tuple(self):
                try:
                    i(arg)
                except Unsub:
                    self.remove(i)
                except Exception:
                    print_exc()

    def __call__(self) -> T | None:
        self.set(self.f())
        return self.arg


def sourced[T](f: Callable[[Val[T]], Coroutine]) -> Val[T]:
    job: Task[Any] | None = None

    def sub():
        nonlocal job
        job = Task(f(val))

    def unsub():
        if job:
            job.cancel()

    val: Val[T] = Val(sub=sub, unsub=unsub)
    return val
