import aiofiles
import asyncio
import pathlib


def run(main):
    loop = asyncio.get_event_loop()
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


# Prefer the run function from the standard library over the custom
# implementation.
run = asyncio.run if hasattr(asyncio, "run") else run
