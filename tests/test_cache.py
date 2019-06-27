import unittest
import unittest.mock

from polynome.model import Cache
from polynome.storage.local import FileSystem
from tests import asynctest
from tests import kerastest


class TestCache(asynctest.AsyncTestCase):

    async def setUpAsync(self) -> None:
        self.storage = unittest.mock.create_autospec(FileSystem)

    @asynctest.unittest_run_loop
    async def test_all(self):
        # Create loaded model.
        m = kerastest.new_model()
        m.model = unittest.mock.MagicMock()

        self.storage.all = asynctest.AsyncGeneratorMock(return_value=[m])
        cache = await Cache.new(storage=self.storage)

        # Put unloaded model into the cache and ensure that it won't be
        # replaced the call to "all".
        cache.models[m.key] = m
        models = [m async for m in cache.all()]

        self.storage.all.assert_called()
        self.assertEqual(models, [m])
        # Ensure all returned models are loaded.
        self.assertTrue(all(map(lambda m: m.loaded, models)))

    @asynctest.unittest_run_loop
    async def test_save(self):
        m1 = kerastest.new_model()

        self.storage.save = asynctest.AsyncMagicMock(return_value=m1)

        cache = await Cache.new(storage=self.storage)
        m2 = await cache.save(m1.name, m1.tag, None)

        self.storage.save.assert_called()
        self.assertEqual(m1, m2)
        self.assertIn(m1.key, cache.models)

    @asynctest.unittest_run_loop
    async def test_delete(self):
        m = kerastest.new_model()

        self.storage.delete = asynctest.AsyncMagicMock()

        cache = await Cache.new(storage=self.storage)
        cache.models[m.key] = m

        await cache.delete(m.name, m.tag)

        self.storage.delete.assert_called()
        self.assertNotIn(m.key, cache.models)

    @asynctest.unittest_run_loop
    async def test_delete_not_found(self):
        m = kerastest.new_model()

        self.storage.delete = asynctest.AsyncMagicMock()

        cache = await Cache.new(storage=self.storage)
        await cache.delete(m.name, m.tag)

        self.storage.delete.assert_called()
        self.assertNotIn(m.key, cache.models)

    @asynctest.unittest_run_loop
    async def test_load(self):
        m1 = kerastest.new_model()
        m1.model = unittest.mock.MagicMock()

        self.storage.load = asynctest.AsyncMagicMock()

        cache = await Cache.new(storage=self.storage)
        cache.models[m1.key] = m1

        m2 = await cache.load(m1.name, m1.tag)

        self.storage.load.assert_not_called()
        self.assertIn(m1.key, cache.models)
        self.assertEqual(m1, m2)

    @asynctest.unittest_run_loop
    async def test_load_not_found(self):
        m1 = kerastest.new_model()

        self.storage.load = asynctest.AsyncMagicMock(return_value=m1)

        cache = await Cache.new(storage=self.storage)
        m2 = await cache.load(m1.name, m1.tag)

        self.storage.load.assert_called()
        self.assertIn(m1.key, cache.models)

        self.assertEqual(m1, m2)


if __name__ == "__main__":
    unittest.main()
