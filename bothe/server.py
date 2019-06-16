import aiohttp
import aiohttp.web
import importlib
import inspect
import logging

import bothe
import bothe.asynclib
import bothe.logging
import bothe.model
import bothe.handlers
import bothe.storage.local


class Server:
    """Serve the models."""

    @classmethod
    async def new(cls, data_root: str, host: str=None, port: str=None,
                  preload: bool=False,
                  strategy: str=bothe.model.Strategy.No.value,
                  logger: logging.Logger=bothe.logging.internal_logger):
        """Create new instance of the server."""

        self = cls()
        self.host = host
        self.port = port

        # TODO: use different execution strategies for models and
        # fallback to the server-default execution strategy.
        loader = bothe.model.Loader(strategy=strategy, logger=logger)

        storage = bothe.storage.local.FileSystem.new(root=data_root,
                                                     loader=loader)

        self.models = await bothe.model.Pool.new(storage=storage, load=preload)

        self.app = aiohttp.web.Application()
        self.app.on_response_prepare.append(self.prepare_response)
        self.app.add_routes([
            aiohttp.web.put(
                "/models/{name}/{tag}",
                bothe.handlers.Push(self.models)),
            aiohttp.web.delete(
                "/models/{name}/{tag}",
                bothe.handlers.Remove(self.models)),
            aiohttp.web.post(
                "/models/{name}/{tag}/predict",
                bothe.handlers.Predict(self.models)),
            aiohttp.web.get(
                "/models",
                bothe.handlers.List(self.models)),
            ])

        logger.info("Server initialization completed")
        return self

    @classmethod
    def start(cls, **kwargs):
        argnames = inspect.getfullargspec(cls.new)
        kv = {k: v for k, v in kwargs.items() if k in argnames.args}

        task = cls.new(**kv)
        s = bothe.asynclib.run(task)
        s.serve()

    async def prepare_response(self, request, response):
        response.headers["Server"] = "Bothe/{0}".format(bothe.__version__)

    def serve(self):
        """Start serving the models.

        Run event loop to handle the requests.
        """
        aiohttp.web.run_app(
            self.app, print=None,
            host=self.host, port=self.port)


if __name__ == "__main__":
    Server().serve()
