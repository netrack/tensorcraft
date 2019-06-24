import aiofiles
import aiohttp
import aiohttp.web
import logging
import pathlib
import humanize
import tarfile
import typing


import polynome.asynclib
import polynome.errors


async def async_progress(path: pathlib.Path, reader: typing.Coroutine) -> bytes:
    def progress(loaded, total, bar_len=30):
        filled_len = int(round(bar_len * loaded / total))
        empty_len = bar_len - filled_len

        loaded = humanize.naturalsize(loaded).replace(" ", "")
        total = humanize.naturalsize(total).replace(" ", "")

        bar = "=" * filled_len + " " * empty_len
        print("[{0}] {1}/{2}\r".format(bar, loaded, total), end="", flush=True)

    total = path.stat().st_size
    loaded = 0

    progress(loaded, total)
    async for chunk in reader:
        yield chunk
        loaded += len(chunk)

    progress(loaded, total)
    print("", flush=True)



class Client:
    """A client to do basic operations remotely

    An asynchronous client used to publish, remove and list
    available models.

    TODO: move the client implementation into the standalone repo.

    Attributes:
        service_url -- service endpoint
    """

    def __init__(self, service_url: str):
        self.service_url = service_url

    async def push(self, name: str, tag: str, path: pathlib.Path):
        """Push the model to the server.

        The model is expected to be a tarball with in a SaveModel
        format.
        """
        if not path.exists():
            raise ValueError("{0} does not exist".format(path))
        if not tarfile.is_tarfile(str(path)):
            raise ValueError("{0} is not a tar file".format(path))

        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)
            reader = async_progress(path, polynome.asynclib.reader(path))

            await session.put(url, data=reader)

    async def remove(self, name: str, tag: str):
        """Remove the model from the server.

        Method raises error when the model is missing.
        """
        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)
            resp = await session.delete(url)

            if resp.status == aiohttp.web.HTTPNotFound.status_code:
                raise polynome.errors.NotFoundError(name, tag)

    async def list(self):
        """List available models on the server."""
        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models"

            async with session.get(url) as resp:
                return await resp.json()
