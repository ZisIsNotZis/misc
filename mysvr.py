#!/bin/env python
from asyncio import Future, Task, get_event_loop, sleep
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime, format_datetime
from io import IOBase
from math import ceil
from os import O_NONBLOCK, pipe2, splice, close, getenv, stat_result, DirEntry, makedirs
from re import Pattern
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from tarfile import TarInfo
from traceback import format_exc
from typing import IO, Callable
from urllib.parse import unquote


def readable(fd: int | socket) -> Future[None]:
    fu = Future[None]()
    get_event_loop().add_reader(fd, lambda: fu.set_result(None) or get_event_loop().remove_reader(fd))  # type: ignore
    return fu


def writable(fd: int | socket) -> Future[None]:
    fu = Future[None]()
    get_event_loop().add_writer(fd, lambda: fu.set_result(None) or get_event_loop().remove_writer(fd))  # type: ignore
    return fu


# file
async def sendfile(head: str, file: IO, sock: socket) -> None:
    l = file.seek(0, 2)
    sock.send(f'{head}Content-Disposition:attachment;filename="{file.name}"\r\nContent-Length:{l}\r\n\r\n'.encode())
    i = 0
    try:
        while i < l:
            await writable(sock)
            if not (n := sock.sendfile(file, i)):
                break
            i += n
        await sleep(.1)  # TODO:fix this
    except OSError:
        pass


async def recvfile(dat: bytes, sock: socket, file: IO, l: int) -> bytes:
    sock.setblocking(False)
    r, w = pipe2(O_NONBLOCK)

    @lambda _: Task(_())
    async def __():
        i = len(dat)
        while i < l:
            await readable(r)
            if not (n := splice(r, file.fileno(), l - i)):
                break
            i += n
        close(r)

    buf, dat = dat[:l], dat[l:]
    i = file.write(buf)
    while i < l:
        await readable(sock)
        await writable(w)
        if not (n := splice(sock.fileno(), w, l - i)):
            break
        i += n
    close(w)
    return dat


# tar
class Tar(list[DirEntry]):
    pass


def tarhead(name: str, st: stat_result) -> bytes:
    tar = TarInfo(name).replace(mtime=int(st.st_mtime))
    tar.size = st.st_size
    return tar.tobuf(1, 'utf8', 'ignore')


async def sendtar(head: str, uri: str, tar: Tar, sock: socket) -> None:
    tarheads = [tarhead(i.path[len(uri) + 1:], i.stat()) for i in tar]
    buf = f'{head}Content-Disposition:attachment;filename="{uri.rsplit('/')[-1]}.tar"\r\nContent-Length:{sum(map(len, tarheads)) + sum(ceil(i.stat().st_size / 512) for i in tar) * 512 + 1024}\r\n\r\n'.encode()
    try:
        for i, j in zip(tar, tarheads):
            await writable(sock)
            sock.send(buf + j)
            file = open(i.path, 'rb')
            k = 0
            while k < i.stat().st_size:
                await writable(sock)
                if not (n := sock.sendfile(file, k)):
                    break
                k += n
            buf = b'\0' * (-i.stat().st_size % 512)
        await writable(sock)
        sock.send(buf + b'\0' * 1024)
        await sleep(.1)  # TODO:remove this
    except OSError:
        pass


async def recvtar(dat: bytes, sock: socket, uri: str, l: int) -> bytes:
    l = l // 512 - 2
    while l:
        buf, dat = dat[:512], dat[512:]
        ti = TarInfo.frombuf(buf + sock.recv(512 - len(buf)), 'utf8', 'ignore')
        path = uri + ti.path
        makedirs(path.rpartition('/')[0], exist_ok=True)
        dat = await recvfile(dat, sock, open(path, 'wb'), ti.size)
        sock.recv(max(-ti.size % 512 - len(dat), 0))
        dat = dat[-ti.size % 512:]
        l -= 1 + ceil(ti.size / 512)
    sock.recv(max(1024 - len(dat), 0))
    return dat[1024:]


# svr
async def cli(sock: socket) -> None:
    buf, _, dat = sock.recv(1024).partition(b'\r\n\r\n')
    method, uri, _, buf_ = buf.decode().split(maxsplit=3)
    head = {i: unquote(j) for i in buf_.split('\n') for i, _, j in [i.partition(': ')]}
    uri, _, buf_ = uri.partition('?')
    uri = unquote(uri.replace('/..', '').lstrip('/'))
    par = {i: unquote(j) for i in buf_.split('&') for i, _, j in [i.partition('=')]}
    code = '405 Method Not Allowed'
    dat_: bytes | str | IO | Tar | Task = ''
    t = 0.
    try:
        for (meth, pat), f_ in ROUTE.items():
            if meth == method and pat.fullmatch(uri):
                t, f = f_[0](uri, par, head, dat, sock)
                if t <= parsedate_to_datetime(par.get('If-Modified-Since', '1 Jan 1970 08:00:00 GMT')).timestamp():
                    code = '304 Not Modified'
                elif parsedate_to_datetime(par.get('If-Unmodified-Since', '1 Jan 3000 08:00:00')).timestamp() < t:
                    code = '412 Precondition Failed'
                else:
                    dat_ = f()
                    code = '200 OK'
                break
    except FileNotFoundError:
        code = '404 Not Found'
    except Exception:
        code = '500 Internal Server Error'
        dat_ = format_exc()
    print(method, uri, par, code)
    head_ = f'''HTTP/1.1 {code}\r
Last-Modified:{format_datetime(datetime.fromtimestamp(t, timezone.utc), True)}\r
Expires:{format_datetime(datetime.fromtimestamp(t, timezone.utc) + timedelta(hours=1), True)}\r
Cache-Control:max-age=3600\r
'''
    if isinstance(dat_, (IO, IOBase)):
        dat_ = Task(sendfile(head_, dat_, sock))
    elif isinstance(dat_, Tar):
        dat_ = Task(sendtar(head_, uri, dat_, sock))
    if isinstance(dat_, Task):
        dat_.add_done_callback(lambda _: sock.close())
        return
    if isinstance(dat_, str):
        dat_ = dat_.encode()
    sock.send(f'{head_}Content-Length:{len(dat_)}\r\n\r\n'.encode() + dat_)
    sock.close()


async def svr() -> None:
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.setblocking(False)
    s.bind((getenv('HOST', ''), int(getenv('PORT', 8080))))
    s.listen(1)
    while True:
        await readable(s)
        Task(cli(s.accept()[0]))


ROUTE: dict[tuple[str, Pattern[str]], list[Callable[[str, dict[str, str], dict[str, str], bytes, socket], tuple[float, Callable[[], bytes | str | IO | Tar | Task]]]]] = defaultdict(list)
