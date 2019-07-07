import aiohttp.test_utils as aiohttptest
import aiohttp.web
import io
import pathlib
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
        want_value = cryptotest.random_dict()
        resp = aiohttp.web.json_response(want_value)

        async with self.handle_request("GET", "/models", resp) as client:
            recv_value = await client.list()
            self.assertEqual(want_value, recv_value)

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
        resp = aiohttp.web.Response(status=404,
                                    headers={"Error-Code": "Model Not Found"})

        async with self.handle_request("DELETE", path, resp) as client:
            with self.assertRaises(errors.NotFoundError):
                await client.remove(m.name, m.tag)

    @asynctest.unittest_run_loop
    async def test_remove_latest(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/latest"

        resp = aiohttp.web.Response(status=409,
                                    headers={"Error-Code": "Model Latest Tag"})

        async with self.handle_request("DELETE", path, resp) as client:
            with self.assertRaises(errors.LatestTagError):
                await client.remove(m.name, "latest")

    @asynctest.unittest_run_loop
    async def test_status(self):
        want_value = cryptotest.random_dict()
        resp = aiohttp.web.json_response(want_value)

        async with self.handle_request("GET", "/status", resp) as client:
            recv_value = await client.status()
            self.assertEqual(want_value, recv_value)

    @asynctest.unittest_run_loop
    async def test_export_not_found(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"
        resp = aiohttp.web.Response(status=404,
                                    headers={"Error-Code": "Model Not Found"})

        async with self.handle_request("GET", path, resp) as client:
            with self.assertRaises(errors.NotFoundError):
                await client.export(m.name, m.tag, pathlib.Path("/"))

    @asynctest.unittest_run_loop
    async def test_export(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"

        want_value = cryptotest.random_bytes()
        resp = aiohttp.web.Response(body=want_value)

        async with self.handle_request("GET", path, resp) as client:
            writer = io.BytesIO()
            await client.export(m.name, m.tag, asynclib.AsyncIO(writer))

            self.assertEqual(want_value, writer.getvalue())

    @asynctest.unittest_run_loop
    async def test_push(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"
        resp = aiohttp.web.Response(status=201)

        async with self.handle_request("PUT", path, resp) as client:
            b = cryptotest.random_bytes()

            resp = await client.push(m.name, m.tag, io.BytesIO(b))
            self.assertIsNone(resp)

    @asynctest.unittest_run_loop
    async def test_push_latest(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/latest"
        resp = aiohttp.web.Response(status=409,
                                    headers={"Error-Code": "Model Latest Tag"})

        async with self.handle_request("PUT", path, resp) as client:
            with self.assertRaises(errors.LatestTagError):
                b = cryptotest.random_bytes()
                resp = await client.push(m.name, "latest", io.BytesIO(b))

    @asynctest.unittest_run_loop
    async def test_push_duplicate(self):
        m = kerastest.new_model()
        path = f"/models/{m.name}/{m.tag}"
        resp = aiohttp.web.Response(status=409,
                                    headers={"Error-Code": "Model Duplicate"})

        async with self.handle_request("PUT", path, resp) as client:
            with self.assertRaises(errors.DuplicateError):
                b = cryptotest.random_bytes()
                await client.push(m.name, m.tag, io.BytesIO(b))


if __name__ == "__main__":
    unittest.main()
