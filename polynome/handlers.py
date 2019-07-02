import io
import json

import polynome

from aiohttp import web
from typing import Dict

from polynome.storage.base import AbstractStorage
from polynome.errors import InputShapeError, NotFoundError, DuplicateError


class ModelView:
    """View to handle actions related to models.

    Attributes:
        models -- container of models
    """

    def __init__(self, models: AbstractStorage) -> None:
        self.models = models

    def make_error_headers(self, e: ModelError): Dict[str, str]:
        return {"Error-Code": e.error_code}

    async def save(self, req: web.Request) -> web.Response:
        """HTTP handler to save the model.

        Args:
            req -- request with a model tar archive
        """
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        if not req.can_read_body:
            raise web.HTTPBadRequest(text="request has no body")

        try:
            model_stream = io.BytesIO(await req.read())
            await self.models.save(name, tag, model_stream)
        except errors.ModelError as e:
            raise web.HTTPConflict(text=str(e),
                                   headers=self.make_error_headers(e))

        return web.Response(status=web.HTTPCreated.status_code)

    async def predict(self, req: web.Request) -> web.Response:
        """HTTP handler to calculate model predictions.

        Feed model with feature vectors and calculate predictions.

        Args:
            req -- request with a list of feature-vectors
        """
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        if not req.can_read_body:
            raise web.HTTPBadRequest(text="request has no body")

        try:
            body = await req.json()
            model = await self.models.load(name, tag)

            predictions = model.predict(x=body["x"])
        except (InputShapeError, json.decoder.JSONDecodeError) as e:
            raise web.HTTPBadRequest(text=str(e))
        except NotFoundError as e:
            raise web.HTTPNotFound(text=str(e),
                                   headers=self.make_error_headers(e))

        return web.json_response(dict(y=predictions))

    async def list(self, req: web.Request) -> web.Response:
        """HTTP handler to list available models.

        List available models in the storage.

        Args:
            req -- empty request
        """
        models = [m.to_dict() async for m in self.models.all()]
        return web.json_response(list(models))

    async def delete(self, req: web.Request) -> web.Response:
        """Handler that removes a model."""
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        try:
            await self.models.delete(name, tag)
        except NotFoundError as e:
            raise web.HTTPNotFound(text=str(e),
                                   headers=self.make_error_headers(e))
        return web.Response(status=web.HTTPOk.status_code)

    async def export(self, req: web.Request) -> web.Response:
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        try:
            writer = io.BytesIO()
            await self.models.export(name, tag, writer)

            return web.Response(body=writer.getvalue())
        except NotFoundError as e:
            raise web.HTTPNotFound(text=str(e),
                                   headers=self.make_error_headers(e))


class ServerView:
    """Server view to handle actions related to server."""

    def __init__(self, models: AbstractStorage) -> None:
        self.models = models

    async def status(self, req: web.Request) -> web.Response:
        """Handler that returns server status."""
        return web.json_response(dict(
            models=len([m async for m in self.models.all()]),
            server_version=polynome.__version__,
            api_version=polynome.__apiversion__,
            root_path=str(self.models.root_path),
        ))
