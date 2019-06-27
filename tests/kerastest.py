import numpy
import pathlib
import tarfile
import tensorflow as tf
import tempfile
import uuid

from collections import namedtuple

from polynome import asynclib
from polynome import model
from tests import cryptotest


Model = namedtuple("Model", ["name", "tag", "tarpath", "url"])


@asynclib.asynccontextmanager
async def crossentropy_model_tar(name: str, tag: str):
    with tempfile.TemporaryDirectory() as workdir:
        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Activation("tanh"))
        model.compile(optimizer="sgd", loss="binary_crossentropy")

        n = 1000
        x = numpy.random.uniform(0, numpy.pi/2, (n, 1))
        y = numpy.random.randint(2, size=(n, 1))

        model.fit(x, y)

        workpath = pathlib.Path(workdir)
        dest = workpath.joinpath(uuid.uuid4().hex)
        tf.keras.experimental.export_saved_model(model, str(dest))

        # Ensure that model has been created.
        assert dest.exists()

        tarpath = dest.with_suffix(".tar")
        with tarfile.open(str(tarpath), mode="w") as tar:
            tar.add(str(dest), arcname="")

        yield tarpath


def new_model():
    return model.Model.new(name=cryptotest.random_string(),
                           tag=cryptotest.random_string(),
                           root=pathlib.Path("/"))
