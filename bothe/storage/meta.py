import aiorwlock
import pathlib
import tinydb
import typing


class DB:

    def __init__(self, root: str) -> None:
        root = pathlib.Path(root)

        self.lock = aiorwlock.RWLock()
        self.db = tinydb.TinyDB(path=root.joinpath("models.json"),
                                default_table="models")

    async def close(self) -> None:
        async with self.lock.writer_lock:
            self.db.close()

    async def get(self, cond) -> typing.Dict:
        async with self.lock.reader_lock:
            return self.db.get(cond)

    async def all(self) -> typing.Sequence[typing.Dict]:
        async with self.lock.reader_lock:
            return self.db.all()

    async def insert(self, document) -> None:
        async with self.lock.writer_lock:
            self.db.insert(document)

    async def remove(self, cond) -> None:
        async with self.lock.writer_lock:
            self.db.remove(cond)
