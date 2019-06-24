import asyncio
import typing
import unittest
import unittest.mock


class MagicMock(unittest.mock.MagicMock):

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class AsyncGeneratorMock(unittest.mock.MagicMock):
    """Mock async generator type

    This type allows to pass a regular sequence of items in order
    to mimic asynchronous generator.
    """

    def __init__(self, *args, return_value: typing.Sequence = [], **kwargs):
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


def unittest_run_loop(coroutine):
    def test(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine(*args, **kwargs))
    return test


class AsyncTestCase(unittest.TestCase):

    def setUp(self):
        self.__loop = asyncio.get_event_loop()
        self.__loop.run_until_complete(self.setUpAsync())

    def tearDown(self):
        try:
            self.__loop.run_until_complete(self.tearDownAsync())
        finally:
            self.__loop.close()

    async def setUpAsync(self) -> None:
        pass

    async def tearDownAsync(self) -> None:
        pass
