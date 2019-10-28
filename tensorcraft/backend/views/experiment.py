from aiohttp import web


class ExperimentView:
    """View to handle actions related to experiments.

    Attributes:
        experiments -- container of experiments.
    """

    def __init__(self, experiments) -> None:
        self.experiments = experiments

    async def create(self, req: web.Request) -> web.Response:
        return web.Response(status=web.HTTPCreated.status_code)
