import asyncio
import unittest.mock


class MagicMock(unittest.mock.MagicMock):

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


def unittest_run_loop(coroutine):
    def test(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coroutine(*args, **kwargs))
    return test
