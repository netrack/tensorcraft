import aiohttp.test_utils as aiohttptest
import aiohttp.web
import pathlib
import tempfile
import unittest

from polynome import asynclib
from polynome import server
from tests import kerastest
from tests import stringtest


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
        s = await server.Server.new(
            strategy="mirrored",
            pidfile=str(self.workpath.joinpath("k.pid")),
            data_root=str(self.workpath))
        return s.app

    @asynclib.asynccontextmanager
    async def pushed_model(self, name: str = None, tag: str = None) -> str:
        name = name or stringtest.random_string()
        tag = tag or stringtest.random_string()

        async with kerastest.crossentropy_model_tar(name, tag) as tarpath:
            try:
                # Upload the serialized model to the server.
                data = asynclib.reader(tarpath)
                url = "/models/{0}/{1}".format(name, tag)

                # Ensure the model has been uploaded.
                resp = await self.client.put(url, data=data)
                self.assertEqual(resp.status, 201)

                yield kerastest.Model(name, tag, tarpath, url)
            finally:
                await self.client.delete(url)

    @aiohttptest.unittest_run_loop
    async def test_create_twice(self):
        async with self.pushed_model() as m:
            data = asynclib.reader(m.tarpath)

            resp = await self.client.put(m.url, data=data)
            self.assertEqual(resp.status, 409)

    @aiohttptest.unittest_run_loop
    async def test_predict(self):
        async with self.pushed_model() as m:
            data = dict(x=[[1.0]])
            resp = await self.client.post(m.url+"/predict", json=data)
            self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_predict_not_found(self):
        data = dict(x=[[1.0]])
        resp = await self.client.post("/models/x/y/predict", json=data)
        self.assertEqual(resp.status, 404)

    @aiohttptest.unittest_run_loop
    async def test_predict_latest(self):
        async with self.pushed_model() as m1:
            async with self.pushed_model(m1.name) as m2:
                url = "/models/{0}/latest/predict".format(m2.name)
                data = dict(x=[[1.0]])

                resp = await self.client.post(url, json=data)
                self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_list(self):
        async with self.pushed_model() as m:
            resp = await self.client.get("/models")
            self.assertEqual(resp.status, 200)

            data = await resp.json()
            print(data)
            self.assertEqual(2, len(data))

            data = data[0]
            data = dict(name=data.get("name"), tag=data.get("tag"))

            self.assertEqual(data, dict(name=m.name, tag=m.tag))


if __name__ == "__main__":
    unittest.main()
