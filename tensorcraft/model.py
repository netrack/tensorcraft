import aiorwlock
import enum
import contextlib
import copy
import io
import logging
import numpy
import pathlib
import tensorflow as tf
import typing
import uuid

from datetime import datetime

from tensorcraft import errors
from tensorcraft.logging import internal_logger


class Strategy(enum.Enum):
    """Strategy is an execution strategy of the model."""

    No = "no"
    Mirrored = "mirrored"
    MultiWorkerMirrored = "multi_worker_mirrored"


class Tag(enum.Enum):
    """Magic tags of the models."""

    Latest = "latest"


class NoStrategy:
    """A strategy that does nothing additional to the loaded model.

    This strategy used when the computation strategy is not specified.
    """

    def scope(self):
        return contextlib.contextmanager(lambda: (yield None))()


class Loader:
    """Load the model with the specific computation strategy."""

    strategies = {
        Strategy.No: NoStrategy,
        Strategy.Mirrored: tf.distribute.MirroredStrategy,
        Strategy.MultiWorkerMirrored: (
            tf.distribute.experimental.MultiWorkerMirroredStrategy),
    }

    def __init__(self, strategy: str,
                 logger: logging.Logger = internal_logger):
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

    @classmethod
    def new(cls, name: str, tag: str, root: pathlib.Path,
            loader: Loader = None):
        model_id = uuid.uuid4()
        model_path = root.joinpath(model_id.hex)
        model_created_at = datetime.utcnow().timestamp()

        return cls(id=model_id, name=name, tag=tag,
                   created_at=model_created_at,
                   path=model_path, loader=loader)

    def to_dict(self):
        return dict(id=self.id.hex,
                    name=self.name,
                    tag=self.tag,
                    created_at=self.created_at)

    def __init__(self, id: typing.Union[uuid.UUID, str],
                 name: str, tag: str, created_at: float,
                 path: str = None, loader: Loader = None):
        self.id = uuid.UUID(str(id))
        self.name = name
        self.tag = tag
        self.created_at = created_at

        self.loader = loader
        self.path = path
        self.model = None

    def copy(self):
        return copy.copy(self)

    @property
    def key(self):
        return (self.name, self.tag)

    @property
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


class Cache:
    """Cache of models, speeds up the load of models.

    Cache saves models into the in-memory cache and delegates calls
    to the parent storage when the model is not found locally.
    """

    @classmethod
    async def new(cls, storage, preload: bool = False,
                  logger: logging.Logger = internal_logger):
        self = cls()
        self.logger = logger
        self.storage = storage
        self.lock = aiorwlock.RWLock()
        self.models = {}

        self.storage.on_save.append(self.save_to_cache)
        self.storage.on_delete.append(self.delete_from_cache)

        if not preload:
            return self

        async for m in self.all():
            logger.info("Loading {0} model".format(m))
            await self.unsafe_load(m.name, m.tag)

        return self

    @property
    def root_path(self) -> pathlib.Path:
        return self.storage.root_path

    async def all(self) -> typing.Sequence[Model]:
        """List all available models.

        The call puts all retrieved models into the cache. All that models are
        not loaded. So before using them, they must be loaded.
        """
        async with self.lock.reader_lock:
            async for m in self.storage.all():
                if m.key not in self.models:
                    self.models[m.key] = m
                yield m

    async def save(self, name: str, tag: str, model: io.IOBase) -> Model:
        """Save the model and load it into the memory.

        Most likely the saved model will be used in the short period of time,
        therefore it is beneficial to load it right after the save.
        """
        m = await self.storage.save(name, tag, model)
        await self.save_to_cache(m)
        return m

    async def save_to_cache(self, m: Model) -> None:
        async with self.lock.writer_lock:
            self.models[(m.name, m.tag)] = m

    async def delete(self, name: str, tag: str) -> None:
        # This is totally fine to loose the data from the cache but
        # leave it in the storage (due to unexpected error).
        await self.delete_from_cache(name, tag)
        await self.storage.delete(name, tag)

    async def delete_from_cache(self, name: str, tag: str) -> None:
        async with self.lock.writer_lock:
            key = (name, tag)
            if key in self.models:
                del self.models[key]

    async def unsafe_load(self, name: str, tag: str) -> Model:
        """Load the model into the internal cache without acquiring a lock."""
        key = (name, tag)
        if ((key not in self.models) or not self.models[key].loaded):
            self.models[key] = await self.storage.load(name, tag)
        return self.models[key]

    async def load(self, name: str, tag: str) -> Model:
        # Load the model from the parent storage when
        # it is missing in the cache.
        async with self.lock.writer_lock:
            return await self.unsafe_load(name, tag)

    async def export(self, name: str, tag: str, writer: io.IOBase) -> None:
        return await self.storage.export(name, tag, writer)
