import aiohttp.test_utils as aiohttptest
import pathlib
import tempfile
import unittest

from aiohttp.web import Application

from tensorcraft.server import Server
from tensorcraft import tlslib
from tests import cryptotest


class TestServerSSL(aiohttptest.AioHTTPTestCase):

    def setUp(self) -> None:
        self.workdir = tempfile.TemporaryDirectory()

        workpath = pathlib.Path(self.workdir.name)
        keypath, certpath = cryptotest.create_self_signed_cert(workpath)

        self.server_ssl_context = tlslib.create_server_ssl_context(
            tls=True, tlscert=certpath, tlskey=keypath,
        )
        self.client_ssl_context = tlslib.create_client_ssl_context(
            tls=True, tlscert=certpath, tlskey=keypath,
        )

        super().setUp()

    async def tearDownAsync(self) -> None:
        self.workdir.cleanup()

    async def get_application(self) -> Application:
        data_root = pathlib.Path(self.workdir.name).joinpath("non/existing")

        server = await Server.new(
            data_root=data_root,
            pidfile=data_root.joinpath("tensorcraft.pid"),
        )
        return server.app

    async def get_server(self, app: Application) -> aiohttptest.TestServer:
        return aiohttptest.TestServer(
            app, loop=self.loop, ssl=self.server_ssl_context,
        )

    @aiohttptest.unittest_run_loop
    async def test_must_accept_tls(self):
        resp = await self.client.get("/status", ssl=self.client_ssl_context)
        self.assertEqual(resp.status, 200)


if __name__ == "__main__":
    unittest.main()
