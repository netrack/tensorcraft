import aiohttp
import aiohttp.web
import json


class Handler:

    def __init__(self, model):
        self.model = model

    async def handle(self, request):
        req = json.loads(await request.text())
        p = self.model.predict(req)
        return aiohttp.web.Response(text=json.dumps(p.tolist())+"\n")


class Server:

    def __init__(self):
        super().__init__()
        self.app = aiohttp.web.Application()

    def handle(self, model):
        # TODO: implement auto-generated routes.
        self.app.add_routes([
            aiohttp.web.post("/predict", Handler(model).handle)])

    def serve(self):
        aiohttp.web.run_app(self.app)
