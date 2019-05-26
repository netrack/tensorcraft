import aiohttp
import aiohttp.web


class JSONHandler:

    def __init__(self, callable):
        self.callable = callable

    async def __call__(self, request):
        req = await request.json()
        resp = self.callable(req)
        return aiohttp.web.json_response(resp)


class Application:

    def __init__(self):
        self.app = aiohttp.web.Application()

    def handle(self, name, model):
        route = "/models/%(name)s/predict" % {"name": name}
        self.app.add_routes([aiohttp.web.post(route, JSONHandler(model))])

    def run(self, host=None, port=None):
        aiohttp.web.run_app(self.app, host=host, port=port)
