import unittest.mock


class MagicMock(unittest.mock.MagicMock):

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
