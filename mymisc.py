def cdll(name: str) -> typing.Callable[[typing.Callable[P, T]], typing.Callable[P, int]]:
    def cdll(f: typing.Callable[P, T]) -> typing.Callable[P, int]:
        g = getattr(CDLL(name), f.__name__)
        g.argtypes = [f.__annotations__.get(i, c_int) for i in f.__code__.co_varnames[:f.__code__.co_argcount]]
        g.restype = f.__annotations__.get('return', c_int)
        return g

    return cdll


def cache(f: typing.Callable[P, T]) -> typing.Callable[P, T]:
    @functools.wraps(f)
    def cache(*args: P.args, _={}, **kwargs: P.kwargs) -> T:
        if (t := _.get(args, ...)) is ...:
            t = _[args] = f(*args, **kwargs)
        return t
    return cache


def vcache(f: typing.Callable[P, typing.Iterator[T]]) -> typing.Callable[P, list[T]]:
    @functools.wraps(f)
    def vcache(*args: P.args, _={}, **kwargs: P.kwargs) -> list[T]:
        for i in chunk([i for i in args if i not in _]):
            for i, j in zip(i, f(*i, **kwargs)):
                if j is not None:
                    _[i] = j
        return [_.get(i) for i in args]
    return vcache


def chunk(a: list[T], n=8) -> typing.Iterator[list[T]]:
    for i in range(0, len(a), n):
        yield a[i:i + n]
