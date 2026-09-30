import torch
from torch import Tensor


def setsign(self: Tensor, s: Tensor) -> Tensor:
    return self*(s.view(torch.int8)*-2).add_(1)


class Lns(tuple[torch.Tensor, torch.Tensor]):
    __slots__ = ()

    def __new__(cls, x, type: torch.dtype | None = None, dev: torch.device | str | None = None) -> 'Lns':
        return super().__new__(cls, x if isinstance(x, tuple)else (abs(x := torch.as_tensor(x, dtype=type, device=dev)).log_(), x.signbit()))

    def totensor(self, x=None) -> Tensor:
        if x is None:
            x = self
        return setsign(x[0].exp(), x[1]) if isinstance(x, Lns) else x if isinstance(x, Tensor)else torch.as_tensor(x, dtype=self[0].dtype, device=self[0].device)

    def tolns(self, x) -> 'Lns':
        return x if isinstance(x, Lns)else Lns(self.totensor(x))

    def __add__(self, x) -> 'Lns':
        x = self.tolns(x)
        sx = self[1] ^ x[1]
        return Lns((setsign((self[0]-x[0]).abs_().neg_().exp_(), sx).log1p_().add_(self[0].maximum(x[0])), (self[1] < x[1]).bitwise_xor_(x[0] < self[0]).where(sx, self[1])))

    def __radd__(self, x) -> 'Lns':
        return self+x

    def __sub__(self, x) -> 'Lns':
        return self + -self.tolns(x)

    def __rsub__(self, x) -> 'Lns':
        return -self + self.tolns(x)

    def __mul__(self, x) -> 'Lns':
        x = self.tolns(x)
        return Lns((self[0]+x[0], self[1] ^ x[1]))

    def __rmul__(self, x) -> 'Lns':
        return self*x

    def __truediv__(self, x) -> 'Lns':
        x = self.tolns(x)
        return Lns((self[0]-x[0], self[1] ^ x[1]))

    def __rtruediv__(self, x) -> 'Lns':
        x = self.tolns(x)
        return Lns((x[0]-self[0], self[1] ^ x[1]))

    def __mod__(self, x) -> Tensor:
        return self.totensor() % x

    def __rmod__(self, x) -> Tensor:
        return x % self.totensor()

    def __abs__(self) -> 'Lns':
        return Lns((self[0], torch.zeros(self.shape, device=self.device, dtype=torch.bool)))

    def __pos__(self) -> 'Lns':
        return self

    def __neg__(self) -> 'Lns':
        return Lns((self[0], ~self[1]))

    def __pow__(self, x) -> 'Lns':
        return Lns((self[0]*self.totensor(x), self[1]))

    def __le__(self, x) -> Tensor:  # type: ignore
        x = self.tolns(x)
        c = self[0] <= x[0]
        return self[1] & ~c | ~x[1] & c

    def __eq__(self, x) -> Tensor:  # type: ignore
        x = self.tolns(x)
        return (self[0] == x[0]) & (self[1] == x[1])

    def __ne__(self, x) -> Tensor:  # type: ignore
        return ~(self == x)

    def __lt__(self, x) -> Tensor:  # type: ignore
        return (self <= x) & ~(self == x)

    def __gt__(self, x) -> Tensor:  # type: ignore
        return ~(self <= x)

    def __ge__(self, x) -> Tensor:  # type: ignore
        return ~(self <= x) | (self == x)

    def log(self) -> 'Lns':
        return Lns(self[0])

    def exp(self) -> 'Lns':
        return abs(Lns((self.totensor(), self[1])))

    @property
    def shape(self) -> torch.Size:
        return self[0].shape

    def size(self, dim: int | None = None) -> int | torch.Size:
        return self[0].size(dim)

    @property
    def device(self) -> torch.device:
        return self[0].device

    def to(self, dev: torch.device | str | None = None, type: torch.dtype | None = None):
        return Lns((self[0].to(dev, type), self[1].to(dev)))


if __name__ == '__main__':
    a, b, c = torch.randn(3, 10, requires_grad=True)
    A, B, C = map(Lns, (a, b, c))
    print(((a+b-c)*c))
    print(_ := ((A+B-C)*C).totensor())
    _.sum().backward()
