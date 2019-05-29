import aiohttp
import aiohttp.web

import bothe.storage.local
import bothe.handlers


class Server:
    """Serve the models."""

    def __init__(self):
        self.models = bothe.storage.local.FileSystem(".var/lib/bothe")

    def serve(self):
        app = aiohttp.web.Application()
        app.add_routes([
            aiohttp.web.post("/models/{name}/{tag}/predict",
                             bothe.handlers.Predict(self.models)),
            aiohttp.web.get("/models",
                            bothe.handlers.List(self.models)),
            ])
        aiohttp.web.run_app(app)


if __name__ == "__main__":
    Server().serve()
