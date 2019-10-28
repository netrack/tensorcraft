import aiofiles
import io
import pathlib
import tempfile
import unittest
import unittest.mock

from tensorcraft.backend import model
from tensorcraft.backend import modelrt
from tests import asynctest
from tests import kerastest


class TestModelRuntime(asynctest.AsyncTestCase):

    async def setUpAsync(self) -> None:
        self.workdir = tempfile.TemporaryDirectory()
        self.workpath = pathlib.Path(self.workdir.name)

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    @asynctest.unittest_run_loop
    async def test_save(self):
        loader = model.Loader("no")
        fs = modelrt.FsStorage.new(path=self.workpath, loader=loader)

        async with kerastest.crossentropy_model_tar("n", "t") as tarpath:
            async with aiofiles.open(tarpath, "rb") as model_tar:
                stream = io.BytesIO(await model_tar.read())
                m = await fs.save("n", "t", stream)

        d1 = await fs.meta.get(modelrt.query_by_name_and_tag("n", "t"))
        d2 = await fs.meta.get(modelrt.query_by_name_and_tag("n", "latest"))

        self.assertEqual(d1["id"], d2["id"])
        self.assertTrue(m.loaded)


if __name__ == "__main__":
    unittest.main()
