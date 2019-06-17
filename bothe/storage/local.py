import asyncio
import concurrent.futures
import io
import logging
import pathlib
import shutil
import tinydb
import typing
import uuid

import bothe.errors
import bothe.logging
import bothe.model
import bothe.storage.meta

from bothe import asynclib


Model = tinydb.Query()


class FileSystem:
    """Storage of models based on ordinary file system.

    Implementation saves the models as unpacked TensorFlow SaveModel
    under the data root path.
    """

    @classmethod
    def new(cls,
            root: str,
            meta: bothe.storage.meta.DB,
            loader: bothe.model.Loader,
            logger: logging.Logger=bothe.logging.internal_logger):

        self = cls()
        logger.info("Using file storage backing engine")

        self.meta = meta
        self.logger = logger
        self.loader = loader

        self.root = pathlib.Path(root)
        self.models_path = self.root.joinpath("models")

        # Since the construction of this object is performed before the
        # start of the event loop, it is fine to call it just like this.
        self.models_path.mkdir(parents=True, exist_ok=True)

        self.executor = concurrent.futures.ThreadPoolExecutor()
        return self

    def _new_model(self, record: typing.Dict) -> bothe.model.Model:
        path = self.models_path.joinpath(record["id"])
        return bothe.model.Model(path=path, loader=self.loader, **record)

    def await_in_thread(self, task: typing.Coroutine):
        """Run the given function within an instance executor."""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, asynclib.run, task)

    async def all(self) -> typing.Sequence[bothe.model.Model]:
        """List available models and their tags.

        The method returns a list of not loaded models, therefore before using
        them (e.g. for prediction), models must be loaded.
        """
        for record in await self.meta.all():
            path = self.models_path.joinpath(record["id"])
            m = bothe.model.Model(path=path, loader=self.loader, **record)
            yield m

    async def save(self, name: str, tag: str,
                   model: io.IOBase) -> bothe.model.Model:
        """Save the model into the local storage.

        Extracts the TAR archive into the data root directory.
        """
        model_id = uuid.uuid4()
        model_path = self.models_path.joinpath(model_id.hex)

        try:
            task = asynclib.extract_tar(fileobj=model, dest=model_path)
            await self.await_in_thread(task)

            # Now load the model into the memory, to pass all validations.
            self.logger.debug("Ensuring model has correct format")

            m = bothe.model.Model(model_id, name, tag, model_path, self.loader)
            m = await self.await_in_thread(asyncio.coroutine(m.load)())

            # Insert the model metadata only on the last step.
            await self.meta.insert(m.to_dict())

            # Model successfully loaded, so now it can be moved to the original
            # data root directory.
            self.logger.info("Pushing model %s to %s", m, model_path)
            return m

        except Exception as e:
            # In case of an exception, remove the model from the directory
            # and ensure the metadata database does not store any information.
            #
            # The caller have to ensure atomicity of this operation.
            await self.meta.remove(Model.id == model_id)

            task = asynclib.remove_dir(model_path, ignore_errors=True)
            await self.await_in_thread(task)
            raise e

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        try:
            # Model found, remove metadata from the database.
            m = await self._load(name, tag)
            await self.meta.remove(Model.id == m.id)

            # Remove the model data from the storage.
            await self.await_in_thread(asynclib.remove_dir(m.path))

            self.logger.info("Removed model %s:%s", name, tag)
        except FileNotFoundError:
            raise bothe.errors.NotFoundError(name, tag)

    async def _load(self, name: str, tag: str):
        record = await self.meta.get((Model.name == name) & (Model.tag == tag))
        if not record:
            raise bothe.errors.NotFoundError(name, tag)
        return self._new_model(record)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag."""
        m = await self._load(name, tag)
        return self.await_in_thread(asyncio.coroutine(m.load)())
