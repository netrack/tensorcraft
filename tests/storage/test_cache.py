import bothe.asynclib
import tests.asynctest
import unittest
import unittest.mock

from bothe.storage import local


class TestCache(unittest.TestCase):

    def test_all(self):
        storage = unittest.mock.create_autospec(local.FileSystem)
        storage.all = tests.asynctest.MagicMock(return_value=[])

        cache = local.Cache(storage)
        models = bothe.asynclib.run(cache.all())

        storage.all.assert_called()
        self.assertEqual(models, [])



if __name__ == "__main__":
    unittest.main()
