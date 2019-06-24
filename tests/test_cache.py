import unittest
import unittest.mock

from polynome.model import Cache
from polynome.storage.local import FileSystem
from tests import asynctest


class TestCache(unittest.TestCase):

    @asynctest.unittest_run_loop
    async def test_all(self):
        storage = unittest.mock.create_autospec(FileSystem)
        storage.all = asynctest.AsyncGeneratorMock(return_value=[])

        cache = await Cache.new(storage=storage)
        models = [m async for m in cache.all()]

        storage.all.assert_called()
        self.assertEqual(models, [])


if __name__ == "__main__":
    unittest.main()
