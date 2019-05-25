import schema


class Keras:
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
            schema.Optional("backend", default="tensorflow"): str,
        }

    def compile(self, config):
        """Loads the prediction model."""
        # Loading of the keras takes time, therefore perform an import
        # of the plugin only when the plugin is specified in the config.
        import keras
        import numpy

        self.config = config
        self.model = keras.models.load_model(config["path"])
        self.model.summary()

    def predict(self, obj):
        """Generates output predictions for the input samples."""
        # TODO: handle unprepared model.
        return self.model.predict(x=numpy.array(obj))
