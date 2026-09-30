#!/bin/env python
from asyncio import gather, Task
from collections.abc import Buffer
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from functools import reduce
from operator import xor, or_
from os import getenv

import numpy as np
from aiohttp.client import ClientSession, ClientError
from aiohttp.web import RouteTableDef, Request, run_app, Application, Response

OLD = datetime(2000, 1, 1, tzinfo=timezone.utc)
NEW = datetime(3000, 1, 1, tzinfo=timezone.utc)
OLDS = format_datetime(OLD, True)
HTTP: ClientSession | None = None


class Cli:
    def __init__(self, ip: str) -> None:
        self.ip = ip

    async def list(self, uri: str, t: datetime = OLD) -> tuple[datetime, dict[str, tuple[int, datetime]]]:
        global HTTP
        HTTP = HTTP or ClientSession()
        try:
            rsp = await HTTP.get(self.ip + uri, headers={'If-Modified-Since': format_datetime(t, True)})
            if rsp.ok:
                return parsedate_to_datetime(rsp.headers.get('Last-Modified', OLDS)), {i[:-4].partition('">')[2]: (int(j), datetime.fromisoformat(k)) for i in (await _.read())[15:-18].decode().split('</td></tr><tr><td>') for i, j, k in [i.split('</td><td>')]}
        except ClientError:
            pass
        return OLD, {}

    async def get(self, uri: str, t: datetime = OLD) -> tuple[datetime, bytes]:
        global HTTP
        HTTP = HTTP or ClientSession()
        try:
            rsp = await HTTP.get(self.ip + uri, headers={'If-Modified-Since': format_datetime(t, True)})
            if rsp.ok:
                return parsedate_to_datetime(rsp.headers.get('Last-Modified', OLDS)), await rsp.read()
        except ClientError:
            pass
        return OLD, b''

    def post(self, uri: str, dat: Buffer, t: datetime = NEW) -> None:
        global HTTP
        HTTP = HTTP or ClientSession()
        Task(HTTP.post(self.ip + uri, data=memoryview(dat), headers={'If-Unmodified-Since': format_datetime(t, True)}))

    def delete(self, uri: str, t: datetime = NEW) -> None:
        global HTTP
        HTTP = HTTP or ClientSession()
        Task(HTTP.delete(self.ip + uri, headers={'If-Modified-Since': format_datetime(t, True)}))


class Svr(Cli):
    def __init__(self, *cli: Cli):
        super().__init__('')
        self.cli = cli

    async def list(self, uri: str, t: datetime = OLD) -> tuple[datetime, dict[str, tuple[int, datetime]]]:
        dats: list[tuple[datetime, dict[str, tuple[int, datetime]]]] = await gather(*(i.list(uri, t) for i in self.cli))
        dat = reduce(or_, (i[1] for i in dats))
        for i, j in dat.items():
            dat[i] = j[0] * (len(self.cli) - 1), j[1]
        return max(i[0] for i in dats), dat

    async def get(self, uri: str, t: datetime = OLD) -> tuple[datetime, bytes]:
        dats: list[tuple[datetime, bytes]] = await gather(*(i.get(uri, t) for i in self.cli))
        match len(_ := [i for i, j in enumerate(dats) if not j]):
            case 0:
                if reduce(xor, (np.frombuffer(i, 'B') for i in dats[:-1])).view(('S', len(dats[0]))) != dats[-1]:  # type: ignore
                    return OLD, b''
            case 1:
                dats[_[0]] = reduce(xor, (np.frombuffer(i, 'B') for i in dats if i is not None)).view(('S', len(dats[_[0] - 1])))  # type: ignore
                self.cli[_[0]].post(uri, dats[_[0]])
            case _:
                return OLD, b''
        return max(i[0] for i in dats), b''.join(i[1] for i in dats[:-1])

    def post(self, uri: str, dat: Buffer, t: datetime = NEW) -> None:
        arr = np.frombuffer(dat, 'B')
        if _ := -len(arr) % (len(self.cli) - 1):
            arr = np.pad(arr, (0, _))
        arr = arr.reshape(len(self.cli) - 1, -1)
        for cli, arr in zip(self.cli, (*arr, np.bitwise_xor.reduce(arr))):
            cli.post(uri, arr)

    def delete(self, uri: str, t: datetime = NEW) -> None:
        for cli in self.cli:
            cli.delete(uri)


SVR = Svr(*map(Cli, getenv('UP', 'http://localhost:8080,http://localhost:8081,http://localhost:8082').split(',')))
ROUTE = RouteTableDef()


@ROUTE.get('/')
@ROUTE.get('/{_:.*/}')
async def onlist(r: Request) -> Response:
    t, dat = await SVR.list(r.path, r.if_modified_since or OLD)
    return Response(body='<table><tr><td><a href="/' + '</td></tr><tr><td><a href="/'.join(f'{i}">{i}</a></td><td>{j}</td><td>{k}' for i, (j, k) in dat.items()) + '</td></tr></table>', content_type='text/html', headers={'Last-Modified': format_datetime(t, True)})


@ROUTE.get('/{_:.*[^/]}')
async def onget(r: Request) -> Response:
    t, dat = await SVR.get(r.path, r.if_modified_since or OLD)
    return Response(body=dat, status=404 if dat is None else 200, headers={'Content-Disposition': 'attachment;filename="' + r.path.rpartition('/')[-1] + '"', 'Last-Modified': format_datetime(t, True)})


@ROUTE.post('/{_:.*}')
async def onpost(r: Request) -> Response:
    SVR.post(r.path, await r.read(), r.if_unmodified_since or NEW)
    return Response()


@ROUTE.delete('/{_:.*}')
async def ondelete(r: Request) -> Response:
    SVR.delete(r.path, r.if_unmodified_since or NEW)
    return Response()


APP = Application(client_max_size=1 << 32)
APP.add_routes(ROUTE)
run_app(APP, port=8000)
