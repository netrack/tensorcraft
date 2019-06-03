import aiofiles
import aiohttp
import logging
import pathlib
import humanize
import sys
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

    def __init__(self, service_url="http://localhost:8080"):
        self.service_url = service_url

    async def push(self, name: str, tag: str, path: pathlib.Path):
        if not path.exists():
            print("{0} does not exist".format(path))
            return

        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models/{0}/{1}".format(name, tag)
            reader = async_progress(path, async_reader(path))

            print("loading model {0}:{1}".format(name, tag))
            await session.put(url, data=reader)

    async def remove(self, name: str, tag: str):
        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models/{0}/{1}".format(name, tag)
            await session.delete(url)

    async def list(self):
        async with aiohttp.ClientSession() as session:
            url = self.service_url + "/models"

            async with session.get(url) as resp:
                for model in await resp.json():
                    print("{name}:{tag}".format(**model))
