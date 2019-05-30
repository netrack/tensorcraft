import io
import pathlib
import shutil
import tarfile

import tensorflow as tf
import bothe.model


class FileSystem:

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def _model_path(self, name, tag):
        """The full name of the model"""
        modelpath = "%(name)s@%(tag)s" % dict(name=name, tag=tag)
        return str(self.path.joinpath(modelpath))

    def all(self) -> [bothe.model.Model]:
        """List available models and their tags."""
        dirs = [d.name for d in self.path.iterdir() if d.is_dir()]
        return [bothe.model.Model(*d.split("@")) for d in dirs]

    def save(self, name: str, tag: str, model: io.IOBase):
        """Save the model into the local storage."""
        path = self._model_path(name, tag)

        with tarfile.open(fileobj=model, mode="r") as tf:
            tf.extractall(path=path)

    def delete(self, name: str, tag: str):
        """Remove model with the given name and tag."""
        path = self._model_path(name, tag)
        shutil.rmtree(path, ignore_errors=False)

    def load(self, name: str, tag: str) -> bothe.model.Model:
        """Load model with the given name and tag."""
        path = self._model_path(name, tag)
        m = tf.keras.experimental.load_from_saved_model(path)
        return bothe.model.Model(name, tag, m)
