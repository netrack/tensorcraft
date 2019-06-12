import aiohttp.test_utils as aiohttptest
import argparse
import numpy
import pathlib
import tarfile
import tempfile
import tensorflow as tf
import tests.asynctest
import unittest

import bothe.server
import bothe.asynclib


class TestServer(aiohttptest.AioHTTPTestCase):
    """Functional test of the server."""

    def setUp(self) -> None:
        # Preserve the link for the temporary directory in order
        # to prevent the self-destruction of this directory.
        self.tempdir = tempfile.TemporaryDirectory()
        self.temppath = pathlib.Path(self.tempdir.name)
        super().setUp()

    async def tearDownAsync(self) -> None:
        self.tempdir.cleanup()

    def get_config(self) -> argparse.Namespace:
        return argparse.Namespace(
            strategy="mirrored",
            data_root=str(self.temppath.joinpath("data")))

    async def get_application(self):
        """Create the server application."""
        server = bothe.server.Server(self.get_config())
        return server.app

    @aiohttptest.unittest_run_loop
    async def test_push(self):
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Activation("tanh"))
        model.compile(optimizer="sgd", loss="binary_crossentropy")

        n = 1000
        x = numpy.random.uniform(0, numpy.pi/2, (n, 1))
        y = numpy.random.randint(2, size=(n, 1))

        model.fit(x, y)

        dest = self.temppath.joinpath("nn1")
        tf.keras.experimental.export_saved_model(model, str(dest))

        # Ensure that model has been created.
        self.assertTrue(dest.exists())

        tarpath = dest.with_suffix(".tar")
        with tarfile.open(str(tarpath), mode="w") as tar:
            tar.add(str(dest), arcname="")

        self.assertTrue(tarpath.exists())

        # Upload the serialized model to the server.
        data = bothe.asynclib.reader(str(tarpath))
        resp = await self.client.put("/models/nn1/latest", data=data)

        # Ensure the model has been uploaded.
        self.assertEqual(resp.status, 201)

        data = dict(x=[[1.0]])
        resp = await self.client.post("/models/nn1/latest/predict", json=data)
        self.assertEqual(resp.status, 200)
        

if __name__ == "__main__":
    unittest.main()
