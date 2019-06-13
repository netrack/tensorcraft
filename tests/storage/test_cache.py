import tests.asynctest
import unittest
import unittest.mock

import bothe.storage.local as local


class TestCache(unittest.TestCase):

    @tests.asynctest.unittest_run_loop
    @unittest.skip("unable to mock async_generator")
    async def test_all(self):
        storage = unittest.mock.create_autospec(local.FileSystem)
        storage.all = tests.asynctest.MagicMock(return_value=[])

        cache = await local.Cache.new(storage=storage)
        models = [m async for m in cache.all()]

        storage.all.assert_called()
        self.assertEqual(models, [])


if __name__ == "__main__":
    unittest.main()
