import humanize
import pathlib

from typing import Coroutine


async def async_progress(path: pathlib.Path, reader: Coroutine) -> bytes:
    def progress(loaded, total, bar_len=30):
        filled_len = int(round(bar_len * loaded / total))
        empty_len = bar_len - filled_len

        loaded = humanize.naturalsize(loaded).replace(" ", "")
        total = humanize.naturalsize(total).replace(" ", "")

        bar = "=" * filled_len + " " * empty_len
        print(f"[{bar}] {loaded}/{total}\r", end="", flush=True)

    total = path.stat().st_size
    loaded = 0

    progress(loaded, total)
    async for chunk in reader:
        yield chunk
        loaded += len(chunk)

    progress(loaded, total)
    print("", flush=True)
