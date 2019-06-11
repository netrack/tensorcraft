import enum
import contextlib
import logging
import numpy
import tensorflow as tf

import bothe.errors


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

    def load(self, path: str):
        """Load the model by the given path."""
        with self.strategy.scope():
            m = tf.keras.experimental.load_from_saved_model(path)
            self.logger.debug("Model loaded from path %s", path)
            return m


class Model:
    """Machine-leaning model.

    Attributes:
        name -- the name of the model
        tag -- the tag of the model
        path -- the location of the model on file system
        loader -- the model loader
    """

    def __init__(self, name: str, tag: str,
                 path: str=None, loader: Loader=None):
        self.name = name
        self.tag = tag

        self.loader = loader
        self.path = path
        self.model = None

    def load(self):
        """Load the execution model."""
        self.model = self.loader.load(self.path)
        return self

    def predict(self, x):
        if not self.model:
            raise errors.NotLoadedError(self.name, self.tag)

        x = numpy.array(x)

        # Calculate the shape of the input data and validate it with the
        # model parameters. This exception is handled by the server in
        # order to return an appropriate error to the client.
        _, *expected_dims = self.model.input_shape
        _, *actual_dims = x.shape

        if expected_dims != actual_dims:
            raise errors.InputShapeError(expected_dims, actual_dims)

        return self.model.predict(x).tolist()

    def todict(self):
        return dict(name=self.name, tag=self.tag)

    def __str__(self):
        return "Model(name={0}, tag={1})".format(self.name, self.tag)
