from dataclasses import is_dataclass
from types import UnionType
from typing import get_args, is_typeddict, get_origin


def cast[T](val, type_: type[T]) -> T:
    e: list[Exception] = []
    for type_ in get_args(type_) if isinstance(type_, UnionType) else (type_,):
        try:
            if origin := get_origin(type_):
                arg = get_args(type_)
                if origin in (list, set):  # list set
                    return origin(cast(i, arg[0]) for i in val)  # type: ignore
                elif origin is dict:  # dict
                    return {cast(i, arg[0]): cast(j, arg[1]) for i, j in val.items()}  # type: ignore
                elif origin is tuple:  # tuple
                    return tuple(cast(j, arg[min(i, len(arg) - (arg[-1] is ...) - 1)]) for i, j in enumerate(val))  # type: ignore
            elif (issubclass(type_, tuple) or is_typeddict(type_) or is_dataclass(type_)) and (annotation := getattr(type_, '__annotations__', {})):  # namedtuple typeddict dataclass
                if isinstance(val, dict):
                    return type_(**{i: cast(j, annotation[i]) for i, j in val.items()})
                return type_(**{j: cast(i, k) for i, (j, k) in zip(val, annotation.items())})
            return type_(val)  # type: ignore
        except Exception as _:
            e.append(_)
    raise ExceptionGroup('', e)
