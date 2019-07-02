import aiofiles
import aiohttp
import aiohttp.web
import pathlib
import ssl
import tarfile

import polynome
import polynome.asynclib
import polynome.errors

from polynome import arglib
from polynome import tlslib

from typing import Coroutine, Union, Dict, IO
from urllib.parse import urlparse, urlunparse


class Client:
    """A client to do basic operations remotely

    An asynchronous client used to publish, remove and list
    available models.

    TODO: move the client implementation into the standalone repo.

    Attributes:
        service_url -- service endpoint
    """

    default_headers = {"Accept-Version":
                       ">={0}".format(polynome.__apiversion__)}

    def __init__(self, service_url: str,
                 ssl_context: Union[ssl.SSLContext, None] = None):

        # Change the protocol to "HTTPS" if SSL context is given.
        if ssl_context:
            url = urlparse(service_url)
            _, *parts = url
            service_url = urlunparse(["https"]+parts)

        self.service_url = service_url
        self.ssl_context = ssl_context

    @classmethod
    def new(cls, **kwargs):
        ssl_args = arglib.filter_callable_arguments(
            tlslib.create_client_ssl_context, **kwargs)

        ssl_context = tlslib.create_client_ssl_context(**ssl_args)
        self = cls(kwargs.get("service_url"), ssl_context)
        return self

    async def push(self, name: str, tag: str, reader: IO) -> None:
        """Push the model to the server.

        The model is expected to be a tarball with in a SaveModel
        format.
        """
        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)

            await session.put(url, data=reader, headers=self.default_headers,
                              ssl_context=self.ssl_context)

    async def remove(self, name: str, tag: str):
        """Remove the model from the server.

        Method raises error when the model is missing.
        """
        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)
            resp = await session.delete(url, headers=self.default_headers,
                                        ssl_context=self.ssl_context)

            if resp.status == aiohttp.web.HTTPNotFound.status_code:
                raise polynome.errors.NotFoundError(name, tag)

    async def list(self):
        """List available models on the server."""
        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models"

            async with session.get(url, headers=self.default_headers,
                                   ssl_context=self.ssl_context) as resp:
                return await resp.json()

    async def export(self, name: str, tag: str, writer: IO) -> None:
        """Export the model from the server."""
        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)
            resp = await session.get(url)

            if resp.status == aiohttp.web.HTTPNotFound.status_code:
                raise polynome.errors.NotFoundError(name, tag)

            await writer.write(await resp.read())
                

    async def status(self) -> Dict[str, str]:
        async with aiohttp.ClientSession() as session:
            url = "{0}/status".format(self.service_url)
            resp = await session.get(url)
            return await resp.json()
