class mutuple[*Ts](tuple[*Ts]):
    def __init__(self, arg: tuple[*Ts]):
        self._ = list[object](arg)

    def __getitem__(self, item):
        return self._[item]

    def __setitem__(self, key: int, value) -> None:
        self._[key] = value

    def __iter__(self):
        return iter(self._)

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return tuple(self) == (tuple(other) if isinstance(other, mutuple) else other)

    def __lt__(self, other):
        return tuple(self) < (tuple(other) if isinstance(other, mutuple) else other)
