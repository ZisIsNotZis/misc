torch.conv1d(a.unfold(0, r, 1)[:, None], (_ := torch.windows.gaussian(r, std=r/6)[None, None])).mul_(torch.conv1d(a.square().unfold(0, r, 1)[:, None], _.square_()).rsqrt_())[:, 0, 0]

torch.fft.irfft(torch.fft.rfft((_ := a.unfold(0, 10, 1))/_.norm(2, 1, True)).abs().square_())@torch.windows.gaussian(10, std=5/3)


def conv(q, k, v, r=3):
    return (q[:, None]@torch.fft.irfft(torch.fft.rfft(k.T*v.T[:, None]).mul_(torch.fft.rfft(torch.windows.gaussian(len(k), std=r/3)))).T)[:, 0]
