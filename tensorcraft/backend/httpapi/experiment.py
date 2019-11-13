from aiohttp import web

from tensorcraft.backend import experiment
from tensorcraft.backend.httpapi import routing


class ExperimentView:
    """View to handle actions related to experiments.

    Attributes:
        experiments -- container of experiments
    """

    def __init__(self, experiments: experiment.AbstractStorage) -> None:
        self.experiments = experiments

    @routing.urlto("/experiments")
    async def create(self, req: web.Request) -> web.Response:
        """HTTP handler to update (or create when missing) the experiment.

        Args:
            req -- request with an experiment
        """
        if not req.can_read_body:
            raise web.HTTPBadRequest(text="request has no body")

        body = await req.json()
        e = experiment.Experiment.new(**body)

        await self.experiments.save(e)
        return web.json_response(status=web.HTTPCreated.status_code)

    @routing.urlto("/experiments")
    async def list(self, req: web.Request) -> web.Response:
        experiments = [e.asdict() async for e in self.experiments.all()]
        return web.json_response(list(experiments))

    @routing.urlto("/experiments/{name}")
    async def get(self, req: web.Request) -> web.Response:
        name = req.match_info.get("name")
        e = await self.experiments.load(name)

        return web.json_response(e.asdict())

    @routing.urlto("/experiments/{name}/epochs")
    async def create_epoch(self, req: web.Request) -> web.Response:
        name = req.match_info.get("name")

        if not req.can_read_body:
            raise web.HTTPBadRequest(text="request has no body")

        body = await req.json()
        epoch = experiment.Epoch.new(**body)

        await self.exeriments.save_epoch(name, epoch)
        return web.json_response(status=web.HTTPOk.status_code)
