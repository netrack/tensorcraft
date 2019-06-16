import asyncio
import enum
import contextlib
import io
import logging
import numpy
import pathlib
import tensorflow as tf
import typing
import uuid

import bothe.errors
import bothe.logging


class Strategy(enum.Enum):
    """Strategy is an execution strategy of the model."""

    No = "none"
    Mirrored = "mirrored"
    MultiWorkerMirrored = "multi_worker_mirrored"


class NoneStrategy:
    """A strategy that does nothing additional to the loaded model.

    This strategy used when the computation strategy is not specified.
    """

    def scope(self):
        return contextlib.contextmanager(lambda: (yield None))()


class Loader:
    """Load the model with the specific computation strategy."""

    strategies = {
        Strategy.No: NoneStrategy,
        Strategy.Mirrored: tf.distribute.MirroredStrategy,
        Strategy.MultiWorkerMirrored: (
            tf.distribute.experimental.MultiWorkerMirroredStrategy),
    }

    def __init__(self, strategy: str, logger: logging.Logger):
        if Strategy(strategy) not in self.strategies:
            raise ValueError("unknown strategy {0}".format(strategy))

        strategy_class = self.strategies[Strategy(strategy)]
        logger.info("Using '%s' execution strategy", strategy)

        self.logger = logger
        self.strategy = strategy_class()

    def load(self, path: typing.Union[str, pathlib.Path]):
        """Load the model by the given path."""
        with self.strategy.scope():
            m = tf.keras.experimental.load_from_saved_model(str(path))
            self.logger.debug("Model loaded from path %s", path)
            return m


class Model:
    """Machine-leaning model.

    Attributes:
        id -- unique model identifier
        name -- the name of the model
        tag -- the tag of the model
        path -- the location of the model on file system
        loader -- the model loader
    """

    @classmethod
    def from_dict(cls, **kwargs):
        self = cls(**kwargs)
        return self

    def to_dict(self):
        return dict(id=self.id.hex, name=self.name, tag=self.tag)

    def __init__(self, id: typing.Union[uuid.UUID, str],
                 name: str, tag: str, path: str=None, loader: Loader=None):
        self.id = uuid.UUID(str(id))
        self.name = name
        self.tag = tag

        self.loader = loader
        self.path = path
        self.model = None

    def loaded(self):
        """True when the model is loaded and False otherwise."""
        return self.model is not None

    def load(self):
        """Load the execution model."""
        self.model = self.loader.load(self.path)
        return self

    def predict(self, x):
        if not self.model:
            raise errors.NotLoadedError(self.name, self.tag)

        x = numpy.array(x)

        # This check make sense only for models with defined input shapes
        # (for example, when the layer is Dense).
        if hasattr(self.model, "input_shape"):
            # Calculate the shape of the input data and validate it with the
            # model parameters. This exception is handled by the server in
            # order to return an appropriate error to the client.
            _, *expected_dims = self.model.input_shape
            _, *actual_dims = x.shape

            if expected_dims != actual_dims:
                raise errors.InputShapeError(expected_dims, actual_dims)

        return self.model.predict(x).tolist()

    def __str__(self):
        return "{0}:{1}".format(self.name, self.tag)


class Pool:
    """Pool of models, speeds up the load of models.

    Pool saves models into the in-memory cache and delegates calls
    to the parent storage when the model is not found locally.
    """

    @classmethod
    async def new(cls, storage, load: bool=False,
                  logger: logging.Logger=bothe.logging.internal_logger):
        self = cls()
        self.logger = logger
        self.storage = storage
        self.lock = asyncio.Lock()
        self.models = {}

        if not load:
            return self

        async for m in self.all():
            logger.info("Loading {0}:{1} model".format(m.name, m.tag))
            await self.unsafe_load(m.name, m.tag)

        return self

    async def all(self) -> typing.Sequence[Model]:
        """List all available models.

        The call puts all retrieved models into the cache. All that models are
        not loaded. So before using them, they must be loaded.
        """
        async with self.lock:
            self.models = {}

            async for m in self.storage.all():
                self.models[(m.name, m.tag)] = m
                yield m

    async def save(self, name: str, tag: str, model: io.IOBase) -> Model:
        """Save the model and load it into the memory.

        Most likely the saved model will be used in the short period of time,
        therefore it is beneficial to load it right after the save.
        """
        m = await self.storage.save(name, tag, model)
        async with self.lock:
            self.models[(m.name, m.tag)] = m
        return m

    async def delete(self, name: str, tag: str) -> None:
        fullname = (name, tag)
        # This is totally fine to loose the data from the cache but
        # leave it in the storage (due to unexpected error).
        async with self.lock:
            if fullname in self.models:
                del self.models[fullname]
        await self.storage.delete(name, tag)

    async def unsafe_load(self, name: str, tag: str) -> Model:
        """Load the model into the internal cache without acquiring the lock."""
        fullname = (name, tag)
        if ((fullname not in self.models) or
             not self.models[fullname].loaded()):
            self.models[fullname] = await self.storage.load(name, tag)
        return self.models[fullname]

    async def load(self, name: str, tag: str) -> Model:
        # Load the model from the parent storage when
        # it is missing in the cache.
        async with self.lock:
            return await self.unsafe_load(name, tag)
