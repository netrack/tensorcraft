import aiorwlock
import pathlib
import tinydb
import typing
import uuid

from knuckle import asynclib


class DB:

    @classmethod
    def new(cls, path: pathlib.Path):
        self = cls()
        self._rw_lock = aiorwlock.RWLock()
        self._db = tinydb.TinyDB(path=path.joinpath("metadata.json"),
                                default_table="metadata")
        return self

    async def close(self) -> None:
        async with self._rw_lock.writer_lock:
            self._db.close()

    async def get(self, cond) -> typing.Dict:
        async with self._rw_lock.reader_lock:
            return self._db.get(cond)

    async def search(self, cond) -> typing.Dict:
        async with self._rw_lock.reader_lock:
            return self._db.search(cond)

    async def all(self) -> typing.Sequence[typing.Dict]:
        async with self._rw_lock.reader_lock:
            return self._db.all()

    async def insert(self, document: typing.Dict) -> None:
        async with self._rw_lock.writer_lock:
            self._db.insert(document)

    async def upsert(self, document: typing.Dict, cond) -> None:
        async with self._rw_lock.writer_lock:
            self._db.upsert(document, cond)

    async def remove(self, cond) -> None:
        async with self._rw_lock.writer_lock:
            self._db.remove(cond)

    @asynclib.asynccontextmanager
    async def write_locked(self):
        async with self._rw_lock.writer_lock:
            db = DB()
            db._db = self._db
            db._rw_lock = aiorwlock.RWLock(fast=True)
            yield db


def query_by_name_and_tag(name: str, tag: str):
    q = tinydb.Query()
    return (q.name == name) & (q.tag == tag)


def query_by_name(name: str):
    return tinydb.Query.name == name


def query_by_id(id: uuid.UUID):
    return tinydb.Query().id == id
