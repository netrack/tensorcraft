import asyncio
import unittest.mock
import typing


class MagicMock(unittest.mock.MagicMock):

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class AsyncGeneratorMock(unittest.mock.MagicMock):
    """Mock async generator type

    This type allows to pass a regular sequence of items in order
    to mimic asynchronous generator.
    """

    def __init__(self, *args, return_value: typing.Sequence=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.iter = return_value.__iter__()
        self.return_value = self

    def __aiter__(self) -> typing.AsyncGenerator:
        return self

    async def __anext__(self):
        try:
            return self.iter.__next__() 
        except StopIteration:
            raise StopAsyncIteration


class _AsyncContextManager:

    def __init__(self, async_generator):
        self.agen = async_generator.__aiter__()

    async def __aenter__(self):
        return await self.agen.__anext__()

    async def __aexit__(self, typ, value, traceback):
        try:
            await self.agen.__anext__()
        except StopAsyncIteration:
            return False


def asynccontextmanager(func):
    """Simple implementation of async context manager decorator."""
    def _f(*args, **kwargs):
        async_generator = func(*args, **kwargs)
        return _AsyncContextManager(async_generator)
    return _f


def unittest_run_loop(coroutine):
    def test(*args, **kwargs):
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coroutine(*args, **kwargs))
    return test
