#!/bin/env python
from asyncio import Task
from datetime import datetime
from fnmatch import fnmatch
from os import makedirs, stat, scandir, DirEntry
from re import compile
from shutil import rmtree
from socket import socket
from typing import Callable, Iterator, IO

from uvloop import new_event_loop

from mysvr import ROUTE, svr, recvfile, Tar, recvtar


def ls(uri: str, depth: int, prm: dict[str, str]) -> Iterator[DirEntry[str]]:
    for i in scandir(uri):
        if fnmatch(i.name, prm.get('name', '*')) and ((int(prm.get('dir', 1)) and not depth) or not i.is_dir()) and int(prm.get('be', 0)) <= i.stat().st_size <= int(prm.get('se', 0xffffffff)) and int(prm.get('ne', 0)) <= i.stat().st_mtime <= int(prm.get('oe', 0xffffffff)):
            yield i
        if i.is_dir() and depth:
            yield from ls(i.path, depth - 1, prm)


@ROUTE['GET', compile('|.*/')].append
def onlist(uri: str, prm: dict[str, str], head: dict[str, str], dat: bytes, sock: socket) -> tuple[float, Callable[[], str]]:
    _ = list(ls(uri or '.', int(prm.get('depth', 0)), prm))
    return max(i.stat().st_mtime for i in _), lambda: '<table><tr><td><a href="/' + '</td></tr><tr><td><a href="/'.join(f'{i.path}{'/' if i.is_dir() else ''}">{i.path}{'/' if i.is_dir() else ''}</a></td><td>{i.stat().st_size}</td><td>{datetime.fromtimestamp(i.stat().st_mtime)}' for i in (sorted(_, key=lambda i: getattr(i.stat(), prm['sort'])) if 'sort' in prm else _)) + '</td></tr></table>'


@ROUTE['GET', compile('.*[^/]')].append
def onget(uri: str, prm: dict[str, str], head: dict[str, str], dat: bytes, sock: socket) -> tuple[float, Callable[[], Tar | IO]]:
    prm['dir'] = '0'
    try:
        _ = list(ls(uri, int(prm.get('depth', 0)), prm))
        return max(i.stat().st_mtime for i in _), lambda: Tar(_)
    except NotADirectoryError:
        return stat(uri).st_mtime, lambda: open(uri, 'rb')


@ROUTE['POST', compile('.*[^/]')].append
def onpost(uri: str, prm: dict[str, str], head: dict[str, str], dat: bytes, sock: socket) -> tuple[float, Callable[[], Task]]:
    makedirs(uri.rpartition('/')[0] or '.', exist_ok=True)
    return stat(uri).st_mtime, lambda: Task(recvfile(dat, sock, open(uri, 'wb'), int(head['Content-Length'])))


@ROUTE['POST', compile('|.*/')].append
def onuntar(uri: str, prm: dict[str, str], head: dict[str, str], dat: bytes, sock: socket) -> tuple[float, Callable[[], Task]]:
    return stat(uri or '.').st_mtime, lambda: Task(recvtar(dat, sock, uri, int(head['Content-Length'])))


@ROUTE['DELETE', compile('.*')].append
def ondelete(uri: str, prm: dict[str, str], head: dict[str, str], dat: bytes, sock: socket) -> tuple[float, Callable[[], str]]:
    return stat(uri).st_mtime, lambda: rmtree(uri) or ''


new_event_loop().run_until_complete(svr())
