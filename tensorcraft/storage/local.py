import asyncio
import concurrent.futures
import io
import logging
import operator
import pathlib
import typing

import tensorcraft.logging

from tensorcraft import asynclib
from tensorcraft import errors
from tensorcraft import model
from tensorcraft import signal
from tensorcraft.storage import base
from tensorcraft.storage import metadata
from tensorcraft.storage.metadata import (query_by_name,
                                          query_by_name_and_tag,
                                          query_by_id)


class FileSystem(base.AbstractStorage):
    """Storage of models based on ordinary file system.

    Implementation saves the models as unpacked TensorFlow SaveModel
    under the data root path.
    """

    @classmethod
    def new(cls,
            path: pathlib.Path,
            meta: metadata.DB,
            loader: model.Loader,
            logger: logging.Logger = tensorcraft.logging.internal_logger):

        self = cls()
        logger.info("Using file storage backing engine")

        self.meta = meta
        self.logger = logger
        self.loader = loader
        self.models_path = path.joinpath("models")

        self._on_delete = signal.Signal()
        self._on_save = signal.Signal()

        self.models_path.mkdir(parents=True, exist_ok=True)
        self.executor = concurrent.futures.ThreadPoolExecutor()

        return self

    @property
    def on_delete(self) -> signal.Signal:
        return self._on_delete

    @property
    def on_save(self) -> signal.Signal:
        return self._on_save

    @property
    def root_path(self) -> pathlib.Path:
        return self.models_path

    def build_model_from_document(self, document: typing.Dict) -> model.Model:
        path = self.models_path.joinpath(document["id"])
        return model.Model(path=path, loader=self.loader, **document)

    def await_in_thread(self, coro: typing.Coroutine):
        """Run the given function within an instance executor."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, asynclib.run, coro)

    async def all(self) -> typing.Sequence[model.Model]:
        """List available models and their tags.

        The method returns a list of not loaded models, therefore before using
        them (e.g. for prediction), models must be loaded.
        """
        for document in await self.meta.all():
            path = self.models_path.joinpath(document["id"])
            m = model.Model(path=path, loader=self.loader, **document)
            yield m

    async def save_to_meta(self, m: model.Model) -> None:
        async with self.meta.write_locked() as meta:
            if await meta.get(query_by_name_and_tag(m.name, m.tag)):
                self.logger.debug("Model %s already exists", m)

                raise errors.DuplicateError(m.name, m.tag)

            # Insert the model metadata, and update the latest model link.
            await meta.insert(m.to_dict())
            await self.on_save.send(m)

            # Since the saving is happening right now, the latest model
            # will obviously be the current one.
            latest = m.copy()

            latest.tag = model.Tag.Latest.value
            latest.id = m.id

            latest_query = query_by_name_and_tag(latest.name, latest.tag)
            await meta.upsert(latest.to_dict(), latest_query)
            await self.on_save.send(latest)

    async def save(self, name: str, tag: str,
                   stream: io.IOBase) -> model.Model:
        """Save the model into the local storage.

        Extracts the TAR archive into the data directory.
        """
        # Raise error on attempt to save model with the latest tag.
        if tag == model.Tag.Latest.value:
            raise errors.LatestTagError(name, tag)

        m = model.Model.new(name, tag, self.models_path, self.loader)

        try:
            coro = asynclib.extract_tar(fileobj=stream, dest=m.path)
            await self.await_in_thread(coro)

            # Now load the model into the memory, to pass all validations.
            self.logger.debug("Ensuring model has correct format")

            coro = asyncio.coroutine(m.load)()
            m = await self.await_in_thread(coro)

            await self.save_to_meta(m)

            # Model successfully loaded, so now it can be moved to the original
            # data root directory.
            self.logger.info("Pushing model %s to %s", m, m.path)
            return m

        except Exception as e:
            # In case of an exception, remove the model from the directory
            # and ensure the metadata database does not store any information.
            #
            # The caller have to ensure atomicity of this operation.
            await self.meta.remove(query_by_id(m.id))

            coro = asynclib.remove_dir(m.path, ignore_errors=True)
            await self.await_in_thread(coro)
            raise e

    async def delete_from_meta(self, name: str, tag: str) -> model.Model:
        # Model found, remove metadata from the database.
        async with self.meta.write_locked() as meta:
            m = await self.load_from_meta(name, tag)

            await meta.remove(query_by_id(m.id))
            await self.on_delete.send(m.name, m.tag)

            # Remove the "latest" model link.
            query = query_by_name_and_tag(m.name, model.Tag.Latest.value)
            await meta.remove(query)

            # Retrieve a new "latest" model.
            key = operator.itemgetter("created_at")
            document = await meta.latest(query_by_name(m.name), key)

            latest = self.build_model_from_document(document)
            latest.tag = model.Tag.Latest.value

            await meta.insert(latest.to_dict())
            await self.on_delete.send(m.name, model.Tag.Latest.value)
            await self.on_save.send(latest)
        return m

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        if tag == model.Tag.Latest.value:
            raise model.NotFoundError(name, tag)

        try:
            # Remove the model from the metadata database.
            m = await self.delete_from_meta(name, tag)

            # Remove the model data from the file system.
            await self.await_in_thread(asynclib.remove_dir(m.path))

            self.logger.info("Removed model %s:%s", name, tag)
        except FileNotFoundError:
            raise errors.NotFoundError(name, tag)

    async def load_from_meta(self, name: str, tag: str):
        document = await self.meta.get(query_by_name_and_tag(name, tag))
        if not document:
            raise errors.NotFoundError(name, tag)
        return self.build_model_from_document(document)

    async def load(self, name: str, tag: str) -> model.Model:
        """Load model with the given name and tag."""
        m = await self.load_from_meta(name, tag)
        return await self.await_in_thread(asyncio.coroutine(m.load)())

    async def export(self, name: str, tag: str, writer: io.IOBase) -> None:
        """Export serialized model.

        Method writes a serialized TAR to the stream.
        """
        m = await self.load_from_meta(name, tag)

        coro = asynclib.create_tar(fileobj=writer, path=m.path)
        await self.await_in_thread(coro)
