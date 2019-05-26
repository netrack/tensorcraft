import numpy
import schema

import bothe.plugin.base
import bothe.plugin.error


class Keras(bothe.plugin.base.Plugin):
    """Module to serve Keras machine-learning models."""

    def __init__(self):
        super().__init__()
        self.config = None
        self.model = None

    @classmethod
    def config_schema(cls):
        """Configuration parameters of the plugin."""
        return {
            "path": schema.And(str, len),
        }

    def compile(self, config):
        """Loads the prediction model."""
        # Loading of the keras takes time, therefore perform an import
        # of the plugin only when the plugin is specified in the config.
        import keras

        self.config = config
        self.model = keras.models.load_model(config["path"])
        self.model.summary()

    def predict(self, obj):
        """Generates output predictions for the input samples."""
        x = numpy.array(obj)

        # Calculate the shape of the input data and validate it with the
        # model parameters. This exception is handled by the server in
        # order to return an appropriate error to the client.
        _, *expected_dims = self.model.input_shape
        _, *actual_dims = x.shape

        if expected_dims != actual_dims:
            raise bothe.plugin.error.InputShapeError(expected_dims, actual_dims)

        return self.model.predict(x=x).tolist()
