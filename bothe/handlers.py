import aiohttp.web

from bothe.model import Model


class Predict:
    """Handler that calls the model prediction.
    
    Attributes:
        models -- container of models
    """

    def __init__(self, models):
        self.models = models

    async def __call__(self,
                       req=[aiohttp.web.Request]) -> aiohttp.web.Response:
        """HTTP handler to calculate model predictions.

        Feed model with feature vectors and calculate predictions.

        Args:
            req -- request with a list of feature-vectors
        """
        name = req.match_info.get("name")
        tag = req.match_info.get("tag")

        if not req.can_read_body:
            raise aiohttp.web.HTTPBadRequest(text="request has no body")

        body = await req.json()
        model = self.models.load(name, tag)

        predictions = model.predict(x=body["x"])
        return aiohttp.web.json_response(dict(y=predictions))


class List:
    """Handler that lists all available models.

    Attributes:
        storage -- models container
    """

    def __init__(self, models):
        self.models = models

    async def __call__(self,
                       req=[aiohttp.web.Request]) -> aiohttp.web.Response:
        """HTTP handler to list available models.

        List available models in the storage.

        Args:
            req -- empty request
        """
        models = map(lambda m: m.todict(), self.models.all())
        return aiohttp.web.json_response(list(models))
