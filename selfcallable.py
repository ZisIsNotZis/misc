from typing import Callable, ParamSpec

P = ParamSpec('P')
SelfCallable = Callable[P, 'SelfCallable']


def prt(*arg, **kwarg) -> SelfCallable[[object]]:
    print(*arg, **kwarg)
    return prt


prt(1)(2)(3)
