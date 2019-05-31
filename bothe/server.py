import aiohttp
import aiohttp.web

import bothe
import bothe.storage.local
import bothe.handlers


class Server:
    """Serve the models."""

    def __init__(self, config):
        self.models = bothe.storage.local.FileSystem(".var/lib/bothe")
        self.config = config

    async def prepare_response(self, request, response):
        response.headers["Server"] = "Bothe/{0}".format(bothe.__version__)

    def serve(self):
        app = aiohttp.web.Application()
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
        aiohttp.web.run_app(app)


if __name__ == "__main__":
    Server().serve()
