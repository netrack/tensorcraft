import tests.asynctest
import unittest
import unittest.mock

import bothe.storage.local as local


class TestCache(unittest.TestCase):

    @tests.asynctest.unittest_run_loop
    async def test_all(self):
        storage = unittest.mock.create_autospec(local.FileSystem)
        storage.all = tests.asynctest.MagicMock(return_value=[])

        cache = local.Cache(storage)
        models = await cache.all()

        storage.all.assert_called()
        self.assertEqual(models, [])


if __name__ == "__main__":
    unittest.main()
