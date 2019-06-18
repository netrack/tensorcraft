import aiohttp
import aiohttp.web
import inspect
import logging
import pathlib

import knuckle
import knuckle.logging
import knuckle.model
import knuckle.storage.local
import knuckle.storage.meta

from aiojobs.aiohttp import atomic, setup
from knuckle import handlers


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, host: str=None, port: str=None,
                  preload: bool=False,
                  close_timeout: int=10,
                  strategy: str=knuckle.model.Strategy.No.value,
                  logger: logging.Logger=knuckle.logging.internal_logger):
        """Create new instance of the server."""

        self = cls()
        self.host = host
        self.port = port

        # Create a data root directory where all server data is persisted.
        data_root = pathlib.Path(data_root)
        data_root.mkdir(parents=True, exist_ok=True)

        # TODO: use different execution strategies for models and
        # fallback to the server-default execution strategy.
        loader = knuckle.model.Loader(strategy=strategy, logger=logger)

        # A metadata storage with models details.
        meta = knuckle.storage.meta.DB.new(path=data_root)

        storage = knuckle.storage.local.FileSystem.new(
            path=data_root, meta=meta, loader=loader)

        models = await knuckle.model.Cache.new(
            storage=storage, preload=preload)

        self.app = aiohttp.web.Application()
        self.app.on_response_prepare.append(self._prepare_response)
        self.app.on_shutdown.append(cls.wrap_shutdown(meta.close))

        self.app.add_routes([
            aiohttp.web.put(
                "/models/{name}/{tag}",
                atomic(handlers.Push(models))),
            aiohttp.web.delete(
                "/models/{name}/{tag}",
                atomic(handlers.Remove(models))),
            aiohttp.web.post(
                "/models/{name}/{tag}/predict",
                atomic(handlers.Predict(models))),

            aiohttp.web.get("/models", atomic(handlers.List(models))),
            aiohttp.web.get("/status", atomic(handlers.Status()))])

        setup(self.app)
        logger.info("Server initialization completed")

        return self

    async def _prepare_response(self, request, response):
        response.headers["Server"] = "Bothe/{0}".format(knuckle.__version__)

    @classmethod
    def start(cls, **kwargs):
        """Start serving the models.

        Run event loop to handle the requests.
        """
        argnames = inspect.getfullargspec(cls.new)
        kv = {k: v for k, v in kwargs.items() if k in argnames.args}

        async def application_factory():
            s = await cls.new(**kv)
            return s.app

        aiohttp.web.run_app(application_factory(), print=None,
                            host=kv.get("host"), port=kv.get("port"))

    @classmethod
    def wrap_shutdown(cls, awaitable):
        async def on_shutdown(app):
            await awaitable()
        return on_shutdown


if __name__ == "__main__":
    Server().serve()
