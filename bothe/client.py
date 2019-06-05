import aiofiles
import aiohttp
import logging
import pathlib
import humanize
import sys
import tarfile
import typing


async def async_progress(path: pathlib.Path, reader: typing.Coroutine) -> bytes:
    def progress(loaded, total, bar_len=30):
        filled_len = int(round(bar_len * loaded / total))
        empty_len = bar_len - filled_len

        loaded = humanize.naturalsize(loaded).replace(" ", "")
        total = humanize.naturalsize(total).replace(" ", "")

        bar = "=" * filled_len + " " * empty_len
        sys.stdout.write("[{0}] {1}/{2}\r".format(bar, loaded, total))
        sys.stdout.flush()

    total = path.stat().st_size
    loaded = 0

    progress(loaded, total)
    async for chunk in reader:
        yield chunk
        loaded += len(chunk)

    progress(loaded, total)
    sys.stdout.write("\n")
    sys.stdout.flush()


async def async_reader(path: pathlib.Path, chunk_size=64*1024) -> bytes:
    async with aiofiles.open(str(path), "rb") as f:
        chunk = await f.read(chunk_size)
        while len(chunk):
            yield chunk
            chunk = await f.read(chunk_size)


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
            reader = async_progress(path, async_reader(path))

            await session.put(url, data=reader)

    async def remove(self, name: str, tag: str):
        """Remove the model from the server.

        Model raises ModelNotFoundError when the model is missing.
        """
        async with aiohttp.ClientSession() as session:
            url = "{0}/models/{1}/{2}".format(self.service_url, name, tag)
            await session.delete(url)

    async def list(self):
        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models"

            async with session.get(url) as resp:
                for model in await resp.json():
                    print("{name}:{tag}".format(**model))
