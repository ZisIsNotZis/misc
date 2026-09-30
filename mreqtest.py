from asyncio import Task, sleep

from mreq import *


@mreq
def hello(name: str) -> str:
    return f'hello {name}'


@new_event_loop().run_until_complete
@type(init).__call__
async def _():
    await init()
    N = 0
    for _ in range(100):
        @Task
        @type(init).__call__
        async def _():
            nonlocal N
            while True:
                await hello('jack')
                N += 1
    while True:
        await sleep(1)
        print(N)
        N = 0
