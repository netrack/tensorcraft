from aiohttp import web

from tensorcraft.backend.views import routing


class ExperimentView:
    """View to handle actions related to experiments.

    Attributes:
        experiments -- container of experiments.
    """

    def __init__(self, experiments) -> None:
        self.experiments = experiments

    @routing.urlto("/experiments")
    async def create(self, req: web.Request) -> web.Response:
        return web.Response(status=web.HTTPCreated.status_code)

    @routing.urlto("/experiments/{id}")
    async def get(self, req: web.Request) -> web.Response:
        return web.Response(status=web.HTTPOk.status_code)
