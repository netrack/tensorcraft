import aiohttp.test_utils as aiohttptest
import aiohttp.web
import io
import pathlib
import tempfile
import unittest

from polynome import asynclib
from polynome import errors
from polynome.client import Client
from tests import asynctest
from tests import cryptotest
from tests import kerastest


class TestClient(asynctest.AsyncTestCase):

    @asynclib.asynccontextmanager
    async def handle_request(self,
                             method: str,
                             path: str,
                             resp: aiohttp.web.Response = None) -> Client:
        resp = aiohttp.web.Response() if resp is None else resp
        handler_mock = asynctest.AsyncMagicMock(return_value=resp)

        app = aiohttp.web.Application()
        route = aiohttp.web.RouteDef(
            method, path, asynctest.unittest_handler(handler_mock), {})

        app.add_routes([route])

        async with aiohttptest.TestServer(app) as server:
            service_url = str(server.make_url(""))
            yield Client(service_url)

        handler_mock.assert_called()

    @asynctest.unittest_run_loop
    async def test_list(self):
        exp_value = cryptotest.random_dict()
        resp = aiohttp.web.json_response(exp_value)

        async with self.handle_request("GET", "/models", resp) as client:
            recv_value = await client.list()
            self.assertEqual(exp_value, recv_value)

    @asynctest.unittest_run_loop
    async def test_remove(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"

        async with self.handle_request("DELETE", path) as client:
            self.assertIsNone(await client.remove(m.name, m.tag))

    @asynctest.unittest_run_loop
    async def test_remove_not_found(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"
        resp = aiohttp.web.Response(status=404)

        async with self.handle_request("DELETE", path, resp) as client:
            with self.assertRaises(errors.NotFoundError):
                await client.remove(m.name, m.tag)

    @asynctest.unittest_run_loop
    async def test_status(self):
        exp_value = cryptotest.random_dict()
        resp = aiohttp.web.json_response(exp_value)

        async with self.handle_request("GET", "/status", resp) as client:
            recv_value = await client.status()
            self.assertEqual(exp_value, recv_value)

    @asynctest.unittest_run_loop
    async def test_export_not_found(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"
        resp = aiohttp.web.Response(status=404)

        async with self.handle_request("GET", path, resp) as client:
            with self.assertRaises(errors.NotFoundError):
                await client.export(m.name, m.tag, pathlib.Path("/"))

    @asynctest.unittest_run_loop
    async def test_export(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"

        exp_value = cryptotest.random_string(6)
        resp = aiohttp.web.Response(body=exp_value)

        async with self.handle_request("GET", path, resp) as client:
            with tempfile.NamedTemporaryFile("w+") as dest:
                await client.export(m.name, m.tag, dest.name)

                dest.seek(0)
                recv_value = dest.read()
                self.assertEqual(exp_value, recv_value)

    @asynctest.unittest_run_loop
    async def test_push(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"

        async with self.handle_request("PUT", path) as client:
            b = bytes(cryptotest.random_string(1024), "utf-8")

            res = await client.push(m.name, m.tag, io.BytesIO(b))
            self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
