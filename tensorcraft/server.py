import aiohttp
import aiohttp.web
import asyncio
import logging
import pathlib
import pid
import semver

import tensorcraft
import tensorcraft.model
import tensorcraft.storage.local

from aiojobs.aiohttp import atomic, setup
from functools import partial
from typing import Awaitable

from tensorcraft import arglib
from tensorcraft import handlers
from tensorcraft import tlslib
from tensorcraft.logging import internal_logger
from tensorcraft.storage import metadata


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, pidfile: str,
                  host: str = None, port: str = None,
                  preload: bool = False,
                  close_timeout: int = 10,
                  strategy: str = tensorcraft.model.Strategy.No.value,
                  logger: logging.Logger = internal_logger):
        """Create new instance of the server."""

        self = cls()

        pidfile = pathlib.Path(pidfile)
        self.pid = pid.PidFile(piddir=pidfile.parent, pidname=pidfile.name)

        # Create a data root directory where all server data is persisted.
        data_root = pathlib.Path(data_root)
        data_root.mkdir(parents=True, exist_ok=True)

        # TODO: use different execution strategies for models and
        # fallback to the server-default execution strategy.
        loader = tensorcraft.model.Loader(strategy=strategy, logger=logger)

        # A metadata storage with models details.
        meta = metadata.DB.new(path=data_root)

        storage = tensorcraft.storage.local.FileSystem.new(
            path=data_root, meta=meta, loader=loader)

        models = await tensorcraft.model.Cache.new(
            storage=storage, preload=preload)

        self.app = aiohttp.web.Application()

        self.app.on_startup.append(cls.app_callback(self.pid.create))
        self.app.on_response_prepare.append(self._prepare_response)
        self.app.on_shutdown.append(cls.app_callback(meta.close))
        self.app.on_shutdown.append(cls.app_callback(self.pid.close))

        route = partial(route_to, api_version=tensorcraft.__apiversion__)

        models_view = handlers.ModelView(models)
        server_view = handlers.ServerView(models)

        self.app.add_routes([
            aiohttp.web.put(
                "/models/{name}/{tag}", route(models_view.save)),
            aiohttp.web.get(
                "/models/{name}/{tag}", route(models_view.export)),
            aiohttp.web.delete(
                "/models/{name}/{tag}", route(models_view.delete)),
            aiohttp.web.post(
                "/models/{name}/{tag}/predict", route(models_view.predict)),

            aiohttp.web.get("/models", route(models_view.list)),
            aiohttp.web.get("/status", route(server_view.status))])

        setup(self.app)
        logger.info("Server initialization completed")

        return self

    async def _prepare_response(self, request, response):
        server = "Polynome/{0}".format(tensorcraft.__version__)
        response.headers["Server"] = server

    @classmethod
    def start(cls, **kwargs):
        """Start serving the models.

        Run event loop to handle the requests.
        """
        application_args = arglib.filter_callable_arguments(cls.new, **kwargs)

        async def application_factory():
            s = await cls.new(**application_args)
            return s.app

        ssl_args = arglib.filter_callable_arguments(
            tlslib.create_server_ssl_context, **kwargs)
        ssl_context = tlslib.create_server_ssl_context(**ssl_args)

        aiohttp.web.run_app(application_factory(),
                            print=None,
                            ssl_context=ssl_context,
                            host=kwargs.get("host"), port=kwargs.get("port"))

    @classmethod
    def app_callback(cls, awaitable):
        async def on_signal(app):
            coroutine = awaitable()
            if asyncio.iscoroutine(coroutine):
                await coroutine
        return on_signal


def handle_accept_version(req: aiohttp.web.Request, api_version: str):
    default_version = "=={0}".format(api_version)
    req_version = req.headers.get("Accept-Version", default_version)

    try:
        match = semver.match(api_version, req_version)
    except ValueError as e:
        raise aiohttp.web.HTTPNotAcceptable(text=str(e))
    else:
        if not match:
            text = ("accept version {0} does not match API version {1}"
                    ).format(req_version, api_version)
            raise aiohttp.web.HTTPNotAcceptable(text=text)


def accept_version(handler: Awaitable, api_version: str) -> Awaitable:
    async def _f(req: aiohttp.web.Request) -> aiohttp.web.Response:
        handle_accept_version(req, api_version)
        return await handler(req)
    return _f


def route_to(handler: Awaitable, api_version: str) -> Awaitable:
    """Create a route with the API version validation.

    Returns handler decorated with API version check.
    """
    return atomic(accept_version(handler, api_version))
