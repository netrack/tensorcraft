import aiohttp
import aiohttp.web
import numpy
import ssl

import tensorcraft
import tensorcraft.asynclib

from tensorcraft import arglib
from tensorcraft import errors
from tensorcraft import tlslib

from types import TracebackType
from typing import Dict, IO, NamedTuple, Optional, Sequence, Union, Type
from urllib.parse import urlparse, urlunparse


class Session:

    default_headers = {"Accept-Version":
                       ">={0}".format(tensorcraft.__apiversion__)}

    def __init__(self, service_url: str,
                 ssl_context: Union[ssl.SSLContext, None] = None):

        # Change the protocol to "HTTPS" if SSL context is given.
        if ssl_context:
            url = urlparse(service_url)
            _, *parts = url
            service_url = urlunparse(["https"]+parts)

        self.service_url = service_url
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl_context=ssl_context),
            headers=self.default_headers,
        )

    @property
    def default_headers(self) -> Dict:
        return {"Accept-Version": f">={tensorcraft.__apiversion__}"}

    async def __aenter__(self) -> aiohttp.ClientSession:
        return await self.session.__aenter__()

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.session.__aexit__(exc_type, exc_val, exc_tb)

    def url(self, path: str) -> str:
        return f"{self.service_url}/{path}"

    async def close(self) -> None:
        """Close the session and interrupt communication with remote server."""
        await self.session.close()

    @classmethod
    async def new(cls, **kwargs):
        ssl_args = arglib.filter_callable_arguments(
            tlslib.create_client_ssl_context, **kwargs)

        ssl_context = tlslib.create_client_ssl_context(**ssl_args)
        self = cls(kwargs.get("service_url"), ssl_context)
        return self


class Model:
    """A client to do basic model operations remotely

    An asynchronous client used to publish, remove and list
    available models.

    Attributes:
        session -- connection to remote server
    """


    def __init__(self, session: Session) -> None:
        self.session = session

    async def __aenter__(self) -> "Model":
        return self

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]) -> None:
        await self.session.close()

    @classmethod
    async def new(cls, **kwargs):
        return cls(await Session.new(**kwargs))

    def make_error_from_response(self,
                                 resp: aiohttp.web.Response,
                                 success_status=200) -> Optional[Exception]:
        if resp.status != success_status:
            error_code = resp.headers.get("Error-Code", 0)
            return errors.ModelError.from_error_code(error_code)
        return None

    async def push(self, name: str, tag: str, reader: IO) -> None:
        """Push the model to the server.

        The model is expected to be a tarball with in a SaveModel
        format.
        """
        async with self.session as session:
            url = self.session.url(f"models/{name}/{tag}")
            resp = await session.put(url, data=reader)

            error_class = self.make_error_from_response(resp,
                                                        success_status=201)
            if error_class:
                raise error_class(name, tag)

    async def remove(self, name: str, tag: str) -> None:
        """Remove the model from the server.

        Method raises error when the model is missing.
        """
        async with self.session as session:
            url = self.session.url(f"models/{name}/{tag}")
            resp = await session.delete(url)

            error_class = self.make_error_from_response(resp)
            if error_class:
                raise error_class(name, tag)

    async def list(self):
        """List available models on the server."""
        async with self.session as session:
            async with session.get(self.session.url("models")) as resp:
                return await resp.json()

    async def export(self, name: str, tag: str, writer: IO) -> None:
        """Export the model from the server."""
        async with self.session as session:
            resp = await session.get(self.session.url(f"models/{name}/{tag}"))

            error_class = self.make_error_from_response(resp)
            if error_class:
                raise error_class(name, tag)

            await writer.write(await resp.read())

    async def predict(self, name: str, tag: str,
                      x_pred: Union[numpy.array, list]) -> numpy.array:
        """Feed X array to the given model and retrieve prediction."""
        async with self.session as session:
            url = self.session.url(f"models/{name}/{tag}/predict")
            async with session.post(url, json=dict(x=x_pred)) as resp:
                error_class = self.make_error_from_response(resp)
                if error_class:
                    raise error_class(name, tag)

                resp_data = await resp.json()
                return numpy.array(resp_data.get("y"))

    async def status(self) -> Dict[str, str]:
        async with self.session as session:
            resp = await session.get(self.session.url("status"))
            return await resp.json()


class _Metric(NamedTuple):
    name: str
    value: float


class Experiment:
    """A client to do basic experiments operations remotely

    An asynchronous client used to create, remove and update experiments

    Attributes:
        session -- connection to remove server
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    async def create(self, name: str) -> None:
        async with self.session as session:
            await session.post(self.session.url("experiments"),
                               json=dict(name=name))

    async def trace(self,
                    experiment_name: str,
                    metrics: Sequence[_Metric]) -> None:
        async with self.session as session:
            url = self.session.url(f"experiments/{experiment_name}/epochs")
            await session.post(url, json=dict(metrics=metrics))
