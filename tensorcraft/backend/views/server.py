import tensorcraft

from aiohttp import web

from tensorcraft.backend import model


class ServerView:
    """Server view to handle actions related to server."""

    def __init__(self, models: model.AbstractStorage) -> None:
        self.models = models

    async def status(self, req: web.Request) -> web.Response:
        """Handler that returns server status."""
        return web.json_response(dict(
            models=len([m async for m in self.models.all()]),
            server_version=tensorcraft.__version__,
            api_version=tensorcraft.__apiversion__,
            root_path=str(self.models.root_path),
        ))
