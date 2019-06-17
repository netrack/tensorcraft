import aiohttp.test_utils as aiohttptest
import aiohttp.web
import pathlib
import tempfile

from bothe.server import Server


class TestServerStart(aiohttptest.AioHTTPTestCase):

    def setUp(self) -> None:
        self.workdir = tempfile.TemporaryDirectory()
        super().setUp()

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    async def get_application(self) -> aiohttp.web.Application:
        data_root = pathlib.Path(self.workdir.name).joinpath("non/existing")
        server = await Server.new(data_root=data_root)
        return server.app

    @aiohttptest.unittest_run_loop
    async def test_must_create_directory(self):
        resp = await self.client.get("/status")
        self.assertEqual(resp.status, 200)
