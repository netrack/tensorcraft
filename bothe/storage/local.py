import os
import shutil
import tempfile

import tensorflow as tf


class FileSystem:

    def __init__(self, path):
        self.path = path

    def _model_path(self, name, version):
        """The full name of the model"""
        modelpath = "%(name)s@%(version)d" % dict(name=name, version=version)
        return os.path.join(self.path, modelpath)

    def list(self):
        return []

    def push(self, name, version, model):
        """Save the model into the local storage."""
        path = self._model_path(name, version)
        tf.keras.experimental.export_saved_model(model, path)

    def remove(self, name, version):
        """Remove model with the given name and version."""
        path = self._model_path(name, version)
        shutil.rmtree(path, ignore_errors=False)

    def pull(self, name, version):
        """Load model with the given name and version."""
        path = self._model_path(name, version)
        return tf.keras.experimental.load_from_saved_model(path)
