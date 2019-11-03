import aiohttp
import aiohttp.web
import asyncio
import logging
import pathlib
import pid
import semver

import tensorcraft

from aiojobs.aiohttp import atomic, setup
from functools import partial
from typing import Awaitable

from tensorcraft import arglib
from tensorcraft import tlslib
from tensorcraft.backend import httpapi
from tensorcraft.backend import model
from tensorcraft.backend import saving
from tensorcraft.logging import internal_logger


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, pidfile: str,
                  host: str = None, port: str = None,
                  preload: bool = False,
                  close_timeout: int = 10,
                  strategy: str = model.Strategy.No.value,
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
        loader = model.Loader(strategy=strategy, logger=logger)

        storage = saving.FsModelsStorage.new(path=data_root, loader=loader)
        models = await model.Cache.new(storage=storage, preload=preload)

        # Experiments storage based on regular file system.
        experiments = saving.FsExperimentsStorage.new(path=data_root)

        self.app = aiohttp.web.Application(client_max_size=1024**10)

        self.app.on_startup.append(cls.app_callback(self.pid.create))
        self.app.on_response_prepare.append(self._prepare_response)
        self.app.on_shutdown.append(cls.app_callback(storage.close))
        self.app.on_shutdown.append(cls.app_callback(experiments.close))
        self.app.on_shutdown.append(cls.app_callback(self.pid.close))

        route = partial(route_to, api_version=tensorcraft.__apiversion__)

        models_view = httpapi.ModelView(models)
        server_view = httpapi.ServerView(models)
        experiments_view = httpapi.ExperimentView(experiments)

        self.app.add_routes([
            # Model-related endpoints.
            aiohttp.web.get(models_view.list.url, route(models_view.list)),
            aiohttp.web.put(models_view.save.url, route(models_view.save)),
            aiohttp.web.get(models_view.export.url, route(models_view.export)),
            aiohttp.web.delete(models_view.delete.url,
                               route(models_view.delete)),
            aiohttp.web.post(models_view.predict.url,
                             route(models_view.predict)),

            # Experiment-related endpoints.
            aiohttp.web.post(experiments_view.create.url,
                             route(experiments_view.create)),
            aiohttp.web.get(experiments_view.get.url,
                            route(experiments_view.get)),

            # Server-related endpoints.
            aiohttp.web.get(server_view.status.url, route(server_view.status)),
            aiohttp.web.static("/ui", "static"),
        ])

        setup(self.app)
        logger.info("Server initialization completed")

        return self

    async def _prepare_response(self, request, response):
        server = "TensorCraft/{0}".format(tensorcraft.__version__)
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
