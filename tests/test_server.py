import aiohttp.test_utils as aiohttptest
import aiohttp.web
import argparse
import numpy
import pathlib
import tarfile
import tempfile
import tensorflow as tf
import unittest
import uuid

from knuckle import asynclib
from knuckle import server
from tests import asynctest


class TestServer(aiohttptest.AioHTTPTestCase):
    """Functional test of the server."""

    def setUp(self) -> None:
        # Preserve the link for the temporary directory in order
        # to prevent the self-destruction of this directory.
        self.workdir = tempfile.TemporaryDirectory()
        self.workpath = pathlib.Path(self.workdir.name)
        super().setUp()

    async def setUpAsync(self) -> None:
        self.model_name = "nn"
        self.model_tag = "tag"

        self.tarpath = await self.setup_model_tar(self.model_name,
                                                  self.model_tag)

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    async def setup_model_tar(self, name: str, tag: str):
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Activation("tanh"))
        model.compile(optimizer="sgd", loss="binary_crossentropy")

        n = 1000
        x = numpy.random.uniform(0, numpy.pi/2, (n, 1))
        y = numpy.random.randint(2, size=(n, 1))

        model.fit(x, y)

        dest = self.workpath.joinpath(uuid.uuid4().hex)
        tf.keras.experimental.export_saved_model(model, str(dest))

        # Ensure that model has been created.
        self.assertTrue(dest.exists())

        tarpath = dest.with_suffix(".tar")
        with tarfile.open(str(tarpath), mode="w") as tar:
            tar.add(str(dest), arcname="")

        return tarpath

    async def get_application(self) -> aiohttp.web.Application:
        """Create the server application."""
        s = await server.Server.new(
            strategy="mirrored",
            pidfile=str(self.workpath.joinpath("k.pid")),
            data_root=str(self.workpath))
        return s.app

    @asynclib.asynccontextmanager
    async def with_model(self, name: str=None, tag: str=None) -> str:
        try:
            name = name or self.model_name
            tag = tag or self.model_tag

            # Upload the serialized model to the server.
            data = asynclib.reader(self.tarpath)
            url = "/models/{0}/{1}".format(name, tag)

            # Ensure the model has been uploaded.
            resp = await self.client.put(url, data=data)
            self.assertEqual(resp.status, 201)

            yield url
        finally:
            await self.client.delete(url)

    @aiohttptest.unittest_run_loop
    async def test_create_twice(self):
        async with self.with_model() as url:
            data = asynclib.reader(self.tarpath)

            resp = await self.client.put(url, data=data)
            self.assertEqual(resp.status, 409)

    @aiohttptest.unittest_run_loop
    async def test_predict(self):
        async with self.with_model() as url:
            data = dict(x=[[1.0]])
            resp = await self.client.post(url+"/predict", json=data)
            self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_predict_latest(self):
        async with self.with_model("nn1", "1"):
            async with self.with_model("nn1", "2"):
                url = "/models/nn1/latest/predict"
                data = dict(x=[[1.0]])

                resp = await self.client.post(url, json=data)
                self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_list(self):
        async with self.with_model():
            resp = await self.client.get("/models")
            self.assertEqual(resp.status, 200)

            data = await resp.json()
            print(data)
            self.assertEqual(2, len(data))

            data = data[0]
            data = dict(name=data.get("name"), tag=data.get("tag"))

            self.assertEqual(data, dict(name=self.model_name,
                                        tag=self.model_tag))


if __name__ == "__main__":
    unittest.main()
