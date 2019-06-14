import tests.asynctest
import unittest
import unittest.mock

import bothe.model
import bothe.storage.local


class TestPool(unittest.TestCase):

    @tests.asynctest.unittest_run_loop
    async def test_all(self):
        storage = unittest.mock.create_autospec(bothe.storage.local.FileSystem)
        storage.all = tests.asynctest.AsyncGeneratorMock(return_value=[])

        cache = await bothe.model.Pool.new(storage=storage)
        models = [m async for m in cache.all()]

        storage.all.assert_called()
        self.assertEqual(models, [])


if __name__ == "__main__":
    unittest.main()
