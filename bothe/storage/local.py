import asyncio
import concurrent.futures
import functools
import io
import logging
import pathlib
import shutil
import tarfile
import tempfile
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
                 root: str,
                 loader: bothe.model.Loader,
                 logger: logging.Logger=bothe.logging.internal_logger):

        self.root = pathlib.Path(root)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.logger = logger
        self.loader = loader

        # Since the construction of this object is performed before the
        # start of the event loop, it is fine to call it just like this.
        self.root.mkdir(parents=True, exist_ok=True)

        # Temporary directory in order to save here models that where
        # requested to be saved. We need to check if they are valid at
        # first.
        self.temp_root_directory = tempfile.TemporaryDirectory()
        self.temp_root = pathlib.Path(self.temp_root_directory.name)

    def __del__(self):
        self.temp_root_directory.cleanup()

    def model_name(self, name: str, tag: str) -> str:
        """Full name of the model."""
        return "{name}@{tag}".format(name=name, tag=tag)

    def model_path(self, path: pathlib.Path, name: str, tag: str) -> str:
        """Location of the model in the data root directory."""
        fullname = self.model_name(name, tag)
        return str(path.joinpath(fullname))

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
        paths = await self.run(child_dirs, path=self.root)
        for path in paths:
            yield bothe.model.Model(*path.name.split("@"),
                                    path=path, loader=self.loader)

    async def save(self, name: str, tag: str,
                   model: io.IOBase) -> bothe.model.Model:
        """Save the model into the local storage.

        Extracts the TAR archive into the data root directory under the name
        "model_name@model_tag".
        """
        dest = self.model_path(self.root, name, tag)
        temp_dest = self.model_path(self.temp_root, name, tag)

        self.logger.info("Pushing model image %s:%s to %s", name, tag, dest)

        # Extract TAR archive into the temporary directory, load
        # it, and only if the load completes successfully, move
        # the model into the data directory.
        await self.run(extract_tar, fileobj=model, dest=temp_dest)

        self.logger.debug("Ensuring model has correct format")
        # Now load the model into the memory, to pass all validations.
        m = bothe.model.Model(name, tag, path=temp_dest, loader=self.loader)
        m = await self.run(m.load)

        # Model successfully loaded, so now it can be moved to the original
        # data root directory.
        await self.run(shutil.move, src=temp_dest, dst=dest)
        return m

    async def delete(self, name: str, tag: str) -> None:
        """Remove model with the given name and tag."""
        try:
            path = self.model_path(self.root, name, tag)
            await self.run(shutil.rmtree, path, ignore_errors=False)
            self.logger.info("Removed model image %s:%s", name, tag)
        except FileNotFoundError:
            raise bothe.errors.NotFoundError(name, tag)

    async def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag."""
        path = self.model_path(self.root, name, tag)
        m = bothe.model.Model(name, tag, path, self.loader)
        return await self.run(m.load)


def child_dirs(path: pathlib.Path) -> typing.Sequence[pathlib.Path]:
    """Retrieve all child directories of the given directory."""
    return [p for p in path.iterdir() if p.is_dir()]


def extract_tar(fileobj: io.IOBase, dest: str) -> None:
    """Extract content of the TAR archive into the given directory."""
    with tarfile.open(fileobj=fileobj, mode="r") as tf:
        tf.extractall(dest)
