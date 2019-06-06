import asyncio
import unittest

from bothe.storage import local
from tests import asynctest
from unittest import mock


class TestCache(unittest.TestCase):

    def test_all(self):
        storage = mock.create_autospec(local.FileSystem)
        storage.all = asynctest.MagicMock(return_value=[])

        cache = local.Cache(storage)
        models = asyncio.run(cache.all())

        storage.all.assert_called()
        self.assertEqual(models, [])



if __name__ == "__main__":
    unittest.main()
