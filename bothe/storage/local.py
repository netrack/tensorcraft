import asyncio
import concurrent.futures
import functools
import io
import pathlib
import shutil
import tarfile
import tensorflow
import typing

import bothe.model
import bothe.logging


class FileSystem:
    """Storage of models based on ordinary file system.

    Implementation saves the models as unpacked TensorFlow SaveModel
    under the data root path.
    """

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.strategy = tensorflow.distribute.MirroredStrategy()

        # Since the construction of this object is performed before the
        # start of the event loop, it is fine to call it just like this.
        self.path.mkdir(parents=True, exist_ok=True)

    def _model_path(self, name, tag):
        """The full name of the model"""
        modelpath = "{name}@{tag}".format(name=name, tag=tag)
        return str(self.path.joinpath(modelpath))

    def run(self, func, *args, **kwargs):
        """Run the given function within an instance executor."""
        f = functools.partial(func, *args, **kwargs)
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(self.executor, f)

    async def all(self) -> typing.Sequence[bothe.model.Model]:
        """List available models and their tags.

        The method returns a list of not loaded models, therefore
        before using them model must be loaded.
        """
        paths = await self.run(child_dirs, path=self.path)
        return [bothe.model.Model(*path.name.split("@")) for path in paths]

    async def save(self, name: str, tag: str, model: io.IOBase) -> None:
        """Save the model into the local storage.

        Extracts the TAR archive into the data root directory
        under the name "model_name@model_tag".
        """
        dest = self._model_path(name, tag)
        bothe.logging.info("Pushing model image %s:%s to %s", name, tag, dest)
        await self.run(extract_tar, fileobj=model, dest=dest)

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        try:
            path = self._model_path(name, tag)
            await self.run(shutil.rmtree, path, ignore_errors=False)
        except FileNotFoundError:
            raise bothe.model.NotFoundError(name, tag)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag.

        Model is loaded using TensorFlow SaveModel format.
        """
        def func(path: str):
            with self.strategy.scope():
                return tensorflow.keras.experimental.load_from_saved_model(
                    path)

        path = self._model_path(name, tag)
        m = await self.run(func, path)
        return bothe.model.Model(name, tag, m)


class Cache:
    """Cache of the models, speeds up the load of models.

    Cache saves models into the in-memory cache and delegates calls
    to the parent storage when the model is not found locally.
    """

    def __init__(self, storage):
        self.storage = storage
        self.lock = asyncio.Lock()
        self.models = {}

    async def all(self) -> typing.Sequence[bothe.model.Model]:
        return await self.storage.all()

    async def save(self, name: str, tag: str, model: io.IOBase) -> None:
        """Save the model and load it into the memory.

        Most likely the saved model will be used in the short period of
        time, therefore it is beneficial to load it right after the save.
        """
        await self.storage.save(name, tag, model)
        await self.load(name, tag)

    async def delete(self, name: str, tag: str) -> None:
        fullname = (name, tag)
        async with self.lock:
            if fullname in self.models:
                del self.models[fullname]
        await self.storage.delete(name, tag)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        fullname = (name, tag)
        # Load the model from the parent storage when
        # it is missing in the cache.
        async with self.lock:
            if fullname not in self.models:
                self.models[fullname] = await self.storage.load(name, tag)
        return self.models[fullname]


def child_dirs(path: pathlib.Path) -> typing.Sequence[pathlib.Path]:
    """Retrieve all child directories of the given directory."""
    return [p for p in path.iterdir() if p.is_dir()]


def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)
