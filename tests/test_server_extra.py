import aiohttp.test_utils as aiohttptest
import aiohttp.web
import pathlib
import tempfile
import unittest

from tensorcraft.server import Server


class TestServerExtra(aiohttptest.AioHTTPTestCase):

    def setUp(self) -> None:
        self.workdir = tempfile.TemporaryDirectory()
        super().setUp()

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    async def get_application(self) -> aiohttp.web.Application:
        data_root = pathlib.Path(self.workdir.name).joinpath("non/existing")

        server = await Server.new(
            data_root=data_root,
            pidfile=data_root.joinpath("tensorcraft.pid"))
        return server.app

    @aiohttptest.unittest_run_loop
    async def test_must_create_directory(self):
        resp = await self.client.get("/status")
        self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_accept_version(self):
        headers = {"Accept-Version": ">=0.0.0"}
        resp = await self.client.get("/status", headers=headers)
        self.assertEqual(resp.status, 200)

    @aiohttptest.unittest_run_loop
    async def test_accept_version_not_accepted(self):
        headers = {"Accept-Version": "==0.0.0"}
        resp = await self.client.get("/status", headers=headers)

        self.assertEqual(resp.status, 406)


if __name__ == "__main__":
    unittest.main()
