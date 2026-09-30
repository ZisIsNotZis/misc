from typing import Callable, TypedDict
from asyncio import Future
from base64 import b85encode
from os import getenv
from os import urandom
from inspect import signature

from uvloop import new_event_loop  # noqa
from gmqtt import Client, Subscription
from orjson import loads, dumps

REQ: dict[str, Callable] = {}
RSP: dict[str, Future] = {}
CID = b85encode(urandom(8)).decode()
MQ = Client(CID)


@lambda _: setattr(MQ, 'on_connect', _)
def _(*_):
    MQ.subscribe([Subscription(f'mreq/{i}', 1) for i in REQ] + [Subscription(f'mreq/{CID}', 1)])


@lambda _: setattr(MQ, 'on_message', _)
def _(_, topic: str, payload: bytes, __, prop: TypedDict("prop", {'user_property': list[tuple[str, str]]})):
    if topic == f'mreq/{CID}':
        RSP.pop(prop['user_property'][0][1]).set_result(loads(payload))
    else:
        MQ.publish(f"mreq/{prop['user_property'][0][0]}", dumps(REQ[topic[5:]](**loads(payload))), 1, user_property=('', prop['user_property'][0][1]))


def mreq[T](f: Callable[..., T]) -> Callable[..., Future[T]]:
    if getenv('SVR', ''):
        REQ[f.__name__] = f

    def _(*_, **__) -> Future:
        rid = b85encode(urandom(8)).decode()
        RSP[rid] = fut = Future()
        MQ.publish(f'mreq/{f.__name__}', dumps(signature(f).bind(*_, **__).arguments), 1, user_property=(CID, rid))
        return fut

    return _


def init():
    return MQ.connect('localhost', keepalive=60)
