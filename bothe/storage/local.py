import os
import shutil
import tempfile

import tensorflow as tf
import bothe.model


class FileSystem:

    def __init__(self, path):
        self.path = path
        os.makedirs(self.path, exist_ok=True)

    def _model_path(self, name, tag):
        """The full name of the model"""
        modelpath = "%(name)s@%(tag)s" % dict(name=name, tag=tag)
        return os.path.join(self.path, modelpath)

    def all(self):
        """List available models and their tags."""
        dirs = [d.name for d in os.scandir(self.path) if d.is_dir()]
        return [bothe.model.Model(*d.split("@")) for d in dirs]

    def push(self, name, tag, model):
        """Save the model into the local storage."""
        path = self._model_path(name, tag)
        tf.keras.experimental.export_saved_model(model, path)

    def remove(self, name, tag):
        """Remove model with the given name and tag."""
        path = self._model_path(name, tag)
        shutil.rmtree(path, ignore_errors=False)

    def load(self, name, tag):
        """Load model with the given name and tag."""
        path = self._model_path(name, tag)
        m = tf.keras.experimental.load_from_saved_model(path)
        return bothe.model.Model(name, tag, m)
