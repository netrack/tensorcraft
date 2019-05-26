import abc


class Plugin(metaclass=abc.ABCMeta):
    """A placeholder of all required plugin methods."""

    @classmethod
    @abc.abstractmethod
    def config_schema(cls):
        """Configuration parameters of the plugin."""
        pass

    @abc.abstractmethod
    def compile(self, config):
        """Compile the model from the configuration."""
        pass


    @abc.abstractmethod
    def predict(self, obj):
        """Generate output predictions for input samples."""
        pass
