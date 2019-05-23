import keras
import numpy
import schema


class Keras:
    """Module to serve Keras machine-learning models."""

    def __init__(self):
        super().__init__()
        self.config = None
        self.model = None

    def schema(self):
        """Configuration parameters of the module."""
        return {
            schema.Optional("keras"): {
                "path": schema.And(str, len),
                schema.Optional("backend", default="tensorflow"): str,
            },
        }

    def prepare(self, config):
        """Loads the prediction model."""
        self.config = config
        self.model = keras.models.load_model(config["keras"]["path"])
        self.model.summary()

    def predict(self, obj):
        """Generates output predictions for the input samples."""
        return self.model.predict(x=numpy.array(obj))
