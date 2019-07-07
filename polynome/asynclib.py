import aiofiles
import asyncio
import io
import pathlib
import tarfile
import shutil

from typing import IO


def run(main):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(main)
    finally:
        loop.close()


async def reader(path: pathlib.Path, chunk_size=64*1024) -> bytes:
    async with aiofiles.open(str(path), "rb") as f:
        chunk = await f.read(chunk_size)
        while len(chunk):
            yield chunk
            chunk = await f.read(chunk_size)


class AsyncIO:

    def __init__(self, io: IO):
        self.io = io

    async def read(self, size=-1):
        return self.io.read(size)

    async def write(self, b):
        return self.io.write(b)


async def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)


async def create_tar(fileobj: io.IOBase, path: str) -> None:
    """Create TAR archive with the data specified by path."""
    with tarfile.open(fileobj=fileobj, mode="w") as tf:
        tf.add(path, arcname="")


async def remove_dir(path: pathlib.Path, ignore_errors: bool = False):
    shutil.rmtree(path, ignore_errors=ignore_errors)


class _AsyncContextManager:

    def __init__(self, async_generator):
        self.agen = async_generator.__aiter__()

    async def __aenter__(self):
        return await self.agen.__anext__()

    async def __aexit__(self, typ, value, traceback):
        try:
            await self.agen.__anext__()
        except StopAsyncIteration:
            return False


def asynccontextmanager(func):
    """Simple implementation of async context manager decorator."""
    def _f(*args, **kwargs):
        async_generator = func(*args, **kwargs)
        return _AsyncContextManager(async_generator)
    return _f


# Prefer the run function from the standard library over the custom
# implementation.
run = asyncio.run if hasattr(asyncio, "run") else run
