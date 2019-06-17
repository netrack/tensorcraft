import aiofiles
import asyncio
import io
import pathlib
import tarfile
import shutil


def run(main):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(main)
    finally:
        loop.close()


async def reader(path: pathlib.Path, chunk_size=64*1024) -> bytes:
    async with aiofiles.open(str(path), "rb") as f:
        chunk = await f.read(chunk_size)
        while len(chunk):
            yield chunk
            chunk = await f.read(chunk_size)


async def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)


async def remove_dir(path: pathlib.Path, ignore_errors: bool=False):
    shutil.rmtree(path, ignore_errors=ignore_errors)


# Prefer the run function from the standard library over the custom
# implementation.
run = asyncio.run if hasattr(asyncio, "run") else run
