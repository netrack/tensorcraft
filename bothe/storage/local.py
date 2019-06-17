import asyncio
import concurrent.futures
import functools
import io
import logging
import pathlib
import shutil
import tarfile
import tempfile
import tinydb
import typing
import uuid

import bothe.errors
import bothe.logging
import bothe.model
import bothe.storage.meta


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

        # Temporary directory in order to save here models that where
        # requested to be saved. We need to check if they are valid at
        # first.
        ## self.temp_root_directory = tempfile.TemporaryDirectory()
        ## self.temp_root = pathlib.Path(self.temp_root_directory.name)
        return self

    def _new_model(self, record: typing.Dict) -> bothe.model.Model:
        path = self.models_path.joinpath(record["id"])
        return bothe.model.Model(path=path, loader=self.loader, **record)

    async def _get_model(self, name: str, tag: str):
        record = await self.meta.get((Model.name == name) & (Model.tag == tag))
        if not record:
            raise bothe.errors.NotFoundError(name, tag)
        return self._new_model(record)

    def run(self, func, *args, **kwargs):
        """Run the given function within an instance executor."""
        f = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, f)

    async def all(self) -> typing.Sequence[bothe.model.Model]:
        """List available models and their tags.

        The method returns a list of not loaded models, therefore before using
        them, models must be loaded.
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

        await self.run(extract_tar, fileobj=model, dest=model_path)

        # Now load the model into the memory, to pass all validations.
        self.logger.debug("Ensuring model has correct format")

        m = bothe.model.Model(model_id, name, tag, model_path, self.loader)
        m = await self.run(m.load)

        await self.meta.insert(m.to_dict())

        # Model successfully loaded, so now it can be moved to the original
        # data root directory.
        self.logger.info("Pushing model %s:%s to %s", name, tag, model_path)
        # await self.run(shutil.move, src=temp_model_path, dst=model_path)
        return m

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        try:
            m = await self._get_model(name, tag)

            # Model found, remove metadata from the database.
            await self.meta.remove(Model.id == m.id)
            # Remove the model data from the storage.
            await self.run(shutil.rmtree, m.path, ignore_errors=False)

            self.logger.info("Removed model %s:%s", name, tag)
        except FileNotFoundError:
            raise bothe.errors.NotFoundError(name, tag)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag."""
        m = await self._get_model(name, tag)
        return await self.run(m.load)


def child_dirs(path: pathlib.Path) -> typing.Sequence[pathlib.Path]:
    """Retrieve all child directories of the given directory."""
    return [p for p in path.iterdir() if p.is_dir()]


def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)
