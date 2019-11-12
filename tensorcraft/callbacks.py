import asyncio
import pathlib
import semver
import tarfile
import tempfile

from tensorflow import keras
from tensorflow.keras import callbacks

from tensorcraft import asynclib
from tensorcraft import client


class _RemoteCallback(callbacks.Callback):
    """Callback with default session for communication with remote server.

    Args:
        service_url -- endpoint to the server
        tls -- true to use TLS
        tlsverify -- use TLS and verify remote
        tlscacert -- trust certs signed only by this CA
        tlscert -- path to TLS certificate file
        tlskey -- path to TLS key file
    """

    def __init__(self,
                 service_url: str = "localhost:5678",
                 tls: bool = False,
                 tlsverify: bool = False,
                 tlscacert: pathlib.Path = "cacert.pem",
                 tlscert: pathlib.Path = "cert.pem",
                 tlskey: pathlib.Path = "key.pem"):
        super().__init__()

        self.service_url = service_url
        self.tls = tls
        self.tlsverify = tlsverify
        self.tlscacert = tlscacert
        self.tlscert = tlscert
        self.tlskey = tlskey

    def new_session(self):
        return client.Session.new(
            service_url=self.service_url, tls=self.tls,
            tlsverify=self.tlsverify, tlscacert=self.tlscacert,
            tlscert=self.tlscert, tlskey=self.tlskey)

    def on_train_begin(self, logs=None) -> None:
        self.loop = asyncio.get_event_loop()
        self.session = self.loop.run_until_complete(self.new_session())

    def on_train_end(self, logs=None) -> None:
        self.loop.run_until_complete(self.session.close())


class ModelCheckpoint(_RemoteCallback):
    """Publish model to server after every epoch.

    Args:
        name -- name of the model, when name is not given, name attribute of
                the model will be used
        tag -- tag of the model, by default is "0.0.0", every iteration will
               bump build version, so on the next epoch version will be
               "0.0.0+build1"; tag must be valid semantic version
    """

    def __init__(self, name: str = None, tag: str = "0.0.0",
                 verbose: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)

        self.name = name
        self.tag = tag
        self.verbose = verbose

    def on_train_begin(self, logs=None) -> None:
        super().on_train_begin(logs)
        self.models = client.Model(self.session)

    def on_epoch_end(self, epoch, logs=None) -> None:
        with tempfile.TemporaryDirectory() as td:
            modelpath = pathlib.Path(td, "model")

            # Pure keras models (in contrast with tf.keras), must be saved
            # into h5 format first and loaded using tf model loader.
            h5path = modelpath.with_suffix(".h5")
            self.model.save(h5path)

            # Now this model can be translated into tf entities and saved
            # into the serving format.
            model = keras.models.load_model(h5path)
            keras.experimental.export_saved_model(model, str(modelpath))

            tarpath = modelpath.with_suffix(".tar")
            with tarfile.open(str(tarpath), mode="w") as tar:
                tar.add(str(modelpath), arcname="")

            asyncreader = asynclib.reader(tarpath)

            # Use explicit name when set, use generated model name instead.
            name = self.name or self.model.name
            tag = semver.bump_build(self.tag)

            if self.verbose > 0:
                print("\nEpoch {0:5d}: pushing model {1}:{2}".
                      format(epoch + 1, name, tag))

            task = self.models.push(name, tag, asyncreader)
            self.loop.run_until_complete(task)

        # Update tag after successful model publish.
        self.tag = tag


class ExperimentCallback(_RemoteCallback):
    """Publish metrics of model on each epoch end.

    Args:
        experiment_name -- name of the experiment used to trace metrics.
    """

    def __init__(self, experiment_name: str, **kwargs) -> None:
        super().__init__(**kwargs)

        self.experiment_name = experiment_name

    def on_train_begin(self, logs=None) -> None:
        super().on_train_begin(logs)
        self.experiemnts = client.Experiment(self.session)

    def on_epoch_end(self, epoch, logs=None) -> None:
        # Add support of non-eager execution.
        metrics = [dict(name=m.name, value=m.result().numpy())
                   for m in self.model.metrics]

        task = self.experiments.trace(experiment_name, metrics)
        self.loop.run_until_complete(task)
