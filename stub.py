from typing import Callable


class stub[**P, T](list[Callable[P, None]]):
    _: dict[str, 'stub'] = {}

    def __init__(self, f: Callable[P, None]):
        super().__init__()
        self.f = f
        self._[f.__name__] = self

    def __call__(self, *arg: P.args, **kwarg: P.kwargs) -> None:
        for f in self:
            f(*arg, **kwarg)


@stub
def onmsg(topic: str, msg: str) -> None: ...


@onmsg.append
def onhbmsg(topic: str, msg: str) -> None:
    if topic == 'hb':
        print('hb123')


@onmsg.append
def ontestmsg(topic: str, msg: str) -> None:
    if topic == 'test':
        print('test456')


onmsg('hb', '')
onmsg('test', '')
