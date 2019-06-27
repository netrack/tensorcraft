import aiohttp
import aiohttp.web
import asyncio
import inspect
import logging
import pathlib
import pid
import semver
import ssl

import polynome
import polynome.model
import polynome.storage.local

from aiojobs.aiohttp import atomic, setup
from functools import partial
from typing import Awaitable

from polynome import arglib
from polynome import handlers
from polynome.logging import internal_logger
from polynome.storage import metadata


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, pidfile: str,
                  host: str = None, port: str = None,
                  preload: bool = False,
                  close_timeout: int = 10,
                  strategy: str = polynome.model.Strategy.No.value,
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
        loader = polynome.model.Loader(strategy=strategy, logger=logger)

        # A metadata storage with models details.
        meta = metadata.DB.new(path=data_root)

        storage = polynome.storage.local.FileSystem.new(
            path=data_root, meta=meta, loader=loader)

        models = await polynome.model.Cache.new(
            storage=storage, preload=preload)

        self.app = aiohttp.web.Application()

        self.app.on_startup.append(cls.app_callback(self.pid.create))
        self.app.on_response_prepare.append(self._prepare_response)
        self.app.on_shutdown.append(cls.app_callback(meta.close))
        self.app.on_shutdown.append(cls.app_callback(self.pid.close))

        route = partial(route_to, api_version=polynome.__apiversion__)

        self.app.add_routes([
            aiohttp.web.put(
                "/models/{name}/{tag}",
                route(handlers.Push(models))),
            aiohttp.web.delete(
                "/models/{name}/{tag}",
                route(handlers.Remove(models))),
            aiohttp.web.post(
                "/models/{name}/{tag}/predict",
                route(handlers.Predict(models))),

            aiohttp.web.get("/models", route(handlers.List(models))),
            aiohttp.web.get("/status", route(handlers.Status()))])

        setup(self.app)
        logger.info("Server initialization completed")

        return self

    async def _prepare_response(self, request, response):
        server = "Polynome/{0}".format(polynome.__version__)
        response.headers["Server"] = server

    @classmethod
    def create_ssl_context(cls,
                           tls: bool = False,
                           tlsverify: bool = False,
                           tlscert: str = None,
                           tlskey: str = None,
                           tlscacert: str = None,
                           logger: logging.Logger = internal_logger):
        """Create SSL context with the given TLS configuration."""
        if not tls and not tlsverify:
            return None

        if not pathlib.Path(tlscert).exists():
            raise FileNotFoundError((
                "could not read certificate '{0}', no such file"
                ).format(tlscert))
        if not pathlib.Path(tlskey).exists():
            raise FileNotFoundError((
                "could not read key '{0}', no such file").format(tlskey))

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(tlscert, tlskey)
        ssl_context.verify_mode = ssl.CERT_NONE

        logger.info("Using transport layer security")

        if not tlsverify:
            return ssl_context
                

        if not pathlib.Path(tlscacert).exists():
            raise FileNotFoundError((
                "could not read certification authority certificate"
                "'{0}', no such file").format(tlscacert))

            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_verify_locations(cafile=tlscacert)
            logger.info("using peer certificates validation")

        return ssl_context

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
            cls.create_ssl_context, **kwargs)

        ssl_context = cls.create_ssl_context(**ssl_args)

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
