import schema
import yaml


class Config:
    """The configuration loader and validator."""

    DEFAULT_FILEPATH = "bothe.yml"

    def __init__(self, plugins):
        super().__init__()

        # The schema of the models configuration, this should include
        # all available plugin configurations.
        models_schema = {
            "name": schema.And(str, len),
        }

        for name, m in plugins.items():
            models_schema.update({schema.Optional(name): m.config_schema()})

        self.schema = schema.Schema({
            "server": {
              schema.Optional("addr", default="localhost"): str,
              schema.Optional("port", default="8080"): int,
            },
            # It is expected to serve multiple models in a single server.
            "models": [models_schema],
        })

    def load(self):
        """Loads the configuration file and validates the content."""
        with open(self.DEFAULT_FILEPATH, "r") as f:
            config_dict = yaml.full_load(f)

        return self.schema.validate(config_dict)


def load(plugins):
    """A code surgar to load the configuration."""
    return Config(plugins).load()
