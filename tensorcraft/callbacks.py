import pathlib
import semver
import tarfile
import tempfile

from tensorflow import keras
from tensorflow.keras import callbacks

from tensorcraft import asynclib
from tensorcraft import client


class ModelCheckpoint(callbacks.Callback):
    """Publish model to server after every epoch.

    Args:
        name -- name of the model, when name is not given, name attribute of the
                model will be used
        tag -- tag of the model, by default is "0.0.0", every iteration will
               bump build version, so on the next epoch version will be
               "0.0.0+build1"; tag must be valid semantic version
        tls -- true to use TLS
        tlsverify -- use TLS and verify remote
        tlscacert -- trust certs signed only by this CA
        tlscert -- path to TLS certificate file
        tlskey -- path to TLS key file
    """

    def __init__(self,
                 name: str = None,
                 tag: str = "0.0.0",
                 verbose: int = 0,
                 service_url: str = "http://localhost:5678",
                 tls: bool = False,
                 tlsverify: bool = False,
                 tlscacert: pathlib.Path = "cacert.pem",
                 tlscert: pathlib.Path = "cert.pem",
                 tlskey: pathlib.Path = "key.pem"):
        super().__init__()

        self.name = name
        self.tag = tag
        self.verbose = verbose
        self.client = client.Client.new(service_url=service_url,
                                        tls=tls,
                                        tlsverify=tlsverify,
                                        tlscacert=tlscacert,
                                        tlscert=tlscert,
                                        tlskey=tlskey)

    def on_epoch_end(self, epoch, logs=None) -> None:
        with tempfile.TemporaryDirectory() as td:
            modelpath = pathlib.Path(td, "model")
            keras.experimental.export_saved_model(self.model, str(modelpath))

            tarpath = modelpath.with_suffix(".tar")
            with tarfile.open(str(tarpath), mode="w") as tar:
                tar.add(str(modelpath), arcname="")

            asyncreader = asynclib.reader(tarpath)

            name = self.name or self.model.name
            tag = semver.bump_build(self.tag)

            if self.verbose > 0:
                print("\nEpoch {0:5d}: pushing model {1}:{2}".
                      format(epoch + 1, name, tag))

            coro = self.client.push(name, tag, asyncreader)
            asynclib.run(coro)

        # Update tag after successfull model publish.
        self.tag = tag
