import aiohttp
import aiohttp.web
import logging

import bothe
import bothe.logging
import bothe.handlers
import bothe.storage.local


class Server:
    """Serve the models."""

    def __init__(self, config):
        storage = bothe.storage.local.FileSystem(path=config.data_root)
        storage = bothe.storage.local.Cache(storage)

        self.models = storage
        self.config = config

    async def prepare_response(self, request, response):
        response.headers["Server"] = "Bothe/{0}".format(bothe.__version__)

    def serve(self):
        #logger = logging.getLogger("aiohttp.server")
        #logger.disabled = True

        app = aiohttp.web.Application(logger=None)
        app.on_response_prepare.append(self.prepare_response)
        app.add_routes([
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
        aiohttp.web.run_app(
            app, print=None,
            host=self.config.host, port=self.config.port)


if __name__ == "__main__":
    Server().serve()
