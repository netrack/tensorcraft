import io
import json

from aiohttp import web
from typing import Union

from tensorcraft import errors
from tensorcraft.backend import model


_ConflictReason = Union[errors.DuplicateError, errors.LatestTagError]


def make_error_response(exc_class, model_exc=errors.ModelError, text=""):
    """Return an exception with a specific error code.

    Use this function to construct an exception with custom headers
    that specify concrete error generated by the server.
    """
    return exc_class(text=str(text),
                     headers={"Error-Code": f"{model_exc.error_code}"})


def make_bad_request_response(text: str) -> web.HTTPException:
    """Return HTTP "bad request" exception."""
    return make_error_response(web.HTTPBadRequest, errors.ModelError, text)


def make_conflict_response(reason: _ConflictReason) -> web.HTTPException:
    """Return HTTP "conflict" exception."""
    return make_error_response(web.HTTPConflict, reason, str(reason))


def make_not_found_response(reason: errors.NotFoundError) -> web.HTTPException:
    """Return HTTP "not found" exception."""
    return make_error_response(web.HTTPNotFound, reason, str(reason))


class ModelView:
    """View to handle actions related to models.

    Attributes:
        models -- container of models
    """

    def __init__(self, models: model.AbstractStorage) -> None:
        self.models = models

    async def save(self, req: web.Request) -> web.Response:
        """HTTP handler to save the model.

        Args:
            req -- request with a model tar archive
        """
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        if not req.can_read_body:
            raise make_bad_request_response(text="request has no body")

        try:
            model_stream = io.BytesIO(await req.read())
            await self.models.save(name, tag, model_stream)
        except errors.ModelError as e:
            raise make_conflict_response(reason=e)

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
            raise make_bad_request_response(text="request has no body")

        try:
            body = await req.json()
            model = await self.models.load(name, tag)

            predictions = model.predict(x=body["x"])
        except (errors.InputShapeError, json.decoder.JSONDecodeError) as e:
            raise make_bad_request_response(text=str(e))
        except errors.NotFoundError as e:
            raise make_not_found_response(reason=e)

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
        except errors.NotFoundError as e:
            raise make_not_found_response(reason=e)
        return web.Response(status=web.HTTPOk.status_code)

    async def export(self, req: web.Request) -> web.Response:
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        try:
            writer = io.BytesIO()
            await self.models.export(name, tag, writer)

            return web.Response(body=writer.getvalue())
        except errors.NotFoundError as e:
            raise make_not_found_response(reason=e)
