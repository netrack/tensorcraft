import pathlib
import tempfile

from tensorflow import keras
from tensorflow.keras import callbacks


class ModelCheckpoint(callbacks.Callback):
    """Publish model to server afer every epoch.

    Args:
        name -- name of the model
        tag -- tag of the model
        tls -- true to use TLS
        tlsverify -- use TLS and verify remote
        tlscacert -- trust certs signed only by this CA
        tlscert -- path to TLS certificate file
        tlskey -- path to TLS key file
    """

    def __init__(self,
                 name: str,
                 tag: str = "0.0.0",
                 service_url: str = "http://localhost:5678",
                 tls: bool = False,
                 tlsverify: bool = False
                 tlscacert: pathlib.Path = "cacert.pem",
                 tlscert: pathlib.Path = "cert.pem",
                 tlskey: pathlib.Path = "key.pem"):
        super().__init__()

        self.name = name
        self.tag = tag
        self.client = Client.new(service_url=service_url,
                                 tls=tls,
                                 tlsverify=tlsverify,
                                 tlscacert=tlscacert,
                                 tlscert=tlscert,
                                 tlskey=tlskey)

    def on_epoch_end(self, epoch, logs=None) -> None:
        with tempfile.TemporaryDirectory() as td:
            keras.experimental.export_save_model(self.model, td.name)

            self.tag = semver.bump_build(self.tag)
            asyncreader = asynclib.reader(td.name)

            coro = self.client.push(self.name, self.tag, asyncreader)
            asynclib.run(coro)
