import asyncio
import concurrent.futures
import io
import logging
import operator
import pathlib
import shutil
import tinydb
import typing

import knuckle.errors
import knuckle.logging

from knuckle import asynclib
from knuckle import model
from knuckle.storage import metadata
from knuckle.storage.metadata import (query_by_name,
                                      query_by_name_and_tag,
                                      query_by_id)


class FileSystem:
    """Storage of models based on ordinary file system.

    Implementation saves the models as unpacked TensorFlow SaveModel
    under the data root path.
    """

    @classmethod
    def new(cls,
            path: pathlib.Path,
            meta: metadata.DB,
            loader: model.Loader,
            logger: logging.Logger=knuckle.logging.internal_logger):

        self = cls()
        logger.info("Using file storage backing engine")

        self.meta = meta
        self.logger = logger
        self.loader = loader
        self.models_path = path.joinpath("models")

        self.on_delete = []
        self.on_save = []

        self.models_path.mkdir(parents=True, exist_ok=True)
        self.executor = concurrent.futures.ThreadPoolExecutor()

        return self

    def build_model_from_document(self, document: typing.Dict) -> model.Model:
        path = self.models_path.joinpath(document["id"])
        return model.Model(path=path, loader=self.loader, **document)

    def await_in_thread(self, task: typing.Coroutine):
        """Run the given function within an instance executor."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, asynclib.run, task)

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

                raise knuckle.errors.DuplicateError(m.name, m.tag)

            # Insert the model metadata, and update the latest model link.
            await meta.insert(m.to_dict())

            # Since the saving is happening right now, the latest model
            # will obviously be the current one.
            latest = m.copy()

            latest.tag = model.Tag.Latest.value
            latest.id = m.id

            latest_query = query_by_name_and_tag(latest.name, latest.tag)
            await meta.upsert(latest.to_dict(), latest_query)

    async def save(self, name: str, tag: str,
                   stream: io.IOBase) -> model.Model:
        """Save the model into the local storage.

        Extracts the TAR archive into the data directory.
        """
        m = model.Model.new(name, tag, self.models_path, self.loader)

        try:
            task = asynclib.extract_tar(fileobj=stream, dest=m.path)
            await self.await_in_thread(task)

            # Now load the model into the memory, to pass all validations.
            self.logger.debug("Ensuring model has correct format")

            task = asyncio.coroutine(m.load)()
            m = await self.await_in_thread(task)

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

            task = asynclib.remove_dir(m.path, ignore_errors=True)
            await self.await_in_thread(task)
            raise e

    async def delete_from_meta(self, name: str, tag: str) -> model.Model:
        # Model found, remove metadata from the database.
        async with self.meta.write_locked() as meta:
            m = await self.load_from_meta(name, tag)

            await meta.remove(query_by_id(m.id))

            # Remove the "latest" model link.
            query = query_by_name_and_tag(m.name, model.Tag.Latest.value)
            await meta.remove(query)

            # Retrieve a new "latest" model.
            key = operator.itemgetter("created_at")
            document = await meta.latest(query_by_name(m.name), key)

            latest = self.build_model_from_document(document)
            latest.tag = model.Tag.Latest.value

            await meta.insert(latest.to_dict())
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
            raise knuckle.errors.NotFoundError(name, tag)

    async def load_from_meta(self, name: str, tag: str):
        document = await self.meta.get(query_by_name_and_tag(name, tag))
        if not document:
            raise knuckle.errors.NotFoundError(name, tag)
        return self.build_model_from_document(document)

    async def load(self, name: str, tag: str) -> model.Model:
        """Load model with the given name and tag."""
        m = await self.load_from_meta(name, tag)
        return await self.await_in_thread(asyncio.coroutine(m.load)())
