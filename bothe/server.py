import aiohttp
import aiohttp.web
import aiojobs.aiohttp
import importlib
import inspect
import logging

import bothe
import bothe.logging
import bothe.model
import bothe.handlers
import bothe.storage.local
import bothe.storage.meta


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, host: str=None, port: str=None,
                  preload: bool=False,
                  close_timeout: int=10,
                  strategy: str=bothe.model.Strategy.No.value,
                  logger: logging.Logger=bothe.logging.internal_logger):
        """Create new instance of the server."""

        self = cls()
        self.host = host
        self.port = port

        self.meta = bothe.storage.meta.DB(root=data_root)

        # TODO: use different execution strategies for models and
        # fallback to the server-default execution strategy.
        loader = bothe.model.Loader(strategy=strategy, logger=logger)

        storage = bothe.storage.local.FileSystem.new(root=data_root,
                                                     meta=self.meta,
                                                     loader=loader)

        self.models = await bothe.model.Cache.new(storage=storage,
                                                 preload=preload)

        self.app = aiohttp.web.Application()
        self.app.on_response_prepare.append(self._prepare_response)
        self.app.on_shutdown.append(self._shutdown)

        self.app.add_routes([
            aiohttp.web.put(
                "/models/{name}/{tag}",
                aiojobs.aiohttp.atomic(bothe.handlers.Push(self.models))),
            aiohttp.web.delete(
                "/models/{name}/{tag}",
                aiojobs.aiohttp.atomic(bothe.handlers.Remove(self.models))),
            aiohttp.web.post(
                "/models/{name}/{tag}/predict",
                aiojobs.aiohttp.atomic(bothe.handlers.Predict(self.models))),
            aiohttp.web.get(
                "/models",
                bothe.handlers.List(self.models)),
            ])

        aiojobs.aiohttp.setup(self.app)

        logger.info("Server initialization completed")
        return self

    async def _prepare_response(self, request, response):
        response.headers["Server"] = "Bothe/{0}".format(bothe.__version__)

    async def _shutdown(self, app):
        await self.meta.close()

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


if __name__ == "__main__":
    Server().serve()
