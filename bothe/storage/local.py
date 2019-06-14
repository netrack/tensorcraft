import asyncio
import concurrent.futures
import functools
import io
import logging
import pathlib
import shutil
import tarfile
import typing

import bothe.errors
import bothe.logging
import bothe.model


class FileSystem:
    """Storage of models based on ordinary file system.

    Implementation saves the models as unpacked TensorFlow SaveModel
    under the data root path.
    """

    def __init__(self,
                 path: str,
                 loader: bothe.model.Loader,
                 logger: logging.Logger=bothe.logging.internal_logger):

        self.path = pathlib.Path(path)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.logger = logger
        self.loader = loader

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
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.executor, f)

    async def all(self) -> typing.Sequence[bothe.model.Model]:
        """List available models and their tags.

        The method returns a list of not loaded models, therefore
        before using them model must be loaded.
        """
        paths = await self.run(child_dirs, path=self.path)
        for path in paths:
            yield bothe.model.Model(*path.name.split("@"),
                                    path=path, loader=self.loader)

    async def save(self, name: str, tag: str, model: io.IOBase) -> None:
        """Save the model into the local storage.

        Extracts the TAR archive into the data root directory
        under the name "model_name@model_tag".
        """
        dest = self._model_path(name, tag)
        self.logger.info("Pushing model image %s:%s to %s", name, tag, dest)
        await self.run(extract_tar, fileobj=model, dest=dest)

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        try:
            path = self._model_path(name, tag)
            await self.run(shutil.rmtree, path, ignore_errors=False)
        except FileNotFoundError:
            raise bothe.errors.NotFoundError(name, tag)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag."""
        path = self._model_path(name, tag)
        m = bothe.model.Model(name, tag, path, self.loader)
        return await self.run(m.load)


def child_dirs(path: pathlib.Path) -> typing.Sequence[pathlib.Path]:
    """Retrieve all child directories of the given directory."""
    return [p for p in path.iterdir() if p.is_dir()]


def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)
