import aiohttp.test_utils as aiohttptest
import aiohttp.web
import argparse
import numpy
import pathlib
import tarfile
import tempfile
import tensorflow as tf
import unittest

import bothe.server
import bothe.asynclib

from tests import asynctest


class TestServer(aiohttptest.AioHTTPTestCase):
    """Functional test of the server."""

    def setUp(self) -> None:
        # Preserve the link for the temporary directory in order
        # to prevent the self-destruction of this directory.
        self.workdir = tempfile.TemporaryDirectory()
        self.workpath = pathlib.Path(self.workdir.name)
        super().setUp()

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    async def get_application(self) -> aiohttp.web.Application:
        """Create the server application."""
        server = await bothe.server.Server.new(
            strategy="mirrored",
            data_root=str(self.workpath))
        return server.app

    @asynctest.asynccontextmanager
    async def with_model(self, name: str, tag: str):
        try:
            model = tf.keras.models.Sequential()
            model.add(tf.keras.layers.Activation("tanh"))
            model.compile(optimizer="sgd", loss="binary_crossentropy")

            n = 1000
            x = numpy.random.uniform(0, numpy.pi/2, (n, 1))
            y = numpy.random.randint(2, size=(n, 1))

            model.fit(x, y)

            dest = self.workpath.joinpath(name)
            tf.keras.experimental.export_saved_model(model, str(dest))

            # Ensure that model has been created.
            self.assertTrue(dest.exists())

            tarpath = dest.with_suffix(".tar")
            with tarfile.open(str(tarpath), mode="w") as tar:
                tar.add(str(dest), arcname="")

            self.assertTrue(tarpath.exists())

            # Upload the serialized model to the server.
            data = bothe.asynclib.reader(str(tarpath))

            url = "/models/{0}/{1}".format(name, tag)
            resp = await self.client.put(url, data=data)

            # Ensure the model has been uploaded.
            self.assertEqual(resp.status, 201)
            yield url
        finally:
            await self.client.delete(url)

    @aiohttptest.unittest_run_loop
    async def test_predict(self):
        async with self.with_model("nn1", "latest") as url:
            data = dict(x=[[1.0]])
            resp = await self.client.post(url+"/predict", json=data)
            self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_list(self):
        async with self.with_model("nn1", "latest"):
            resp = await self.client.get("/models")
            self.assertEqual(resp.status, 200)

            data = await resp.json()
            self.assertEqual(1, len(data))

            data = data[0]
            data.pop("id")

            self.assertEqual(data, dict(name="nn1", tag="latest"))


if __name__ == "__main__":
    unittest.main()
