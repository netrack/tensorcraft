import schema
import yaml


class DuplicateNameError(Exception):
    """Exception raised for duplicating model names in the configuration.

    Attributes:
        name -- duplicating model's name
    """

    def __init__(self, name):
        self.name = name


    def __str__(self):
        return "Duplicate model name '%(name)s' found." % {"name": self.name}


class Config:
    """The configuration loader and validator."""

    DEFAULT_FILEPATH = "bothe.yml"

    def __init__(self, plugins):
        # The schema of the models configuration, this should include
        # all available plugin configurations.
        models_schema = {
            "name": schema.And(str, len),
        }

        for name, m in plugins.items():
            models_schema.update({schema.Optional(name): m.config_schema()})

        self.schema = schema.Schema({
            "server": {
              schema.Optional("host", default="localhost"): str,
              schema.Optional("port", default="8080"): int,
            },
            # It is expected to serve multiple models in a single server.
            "models": [models_schema],
        })

    def load(self):
        """Loads the configuration file and validates the content."""
        with open(self.DEFAULT_FILEPATH, "r") as f:
            config_dict = yaml.full_load(f)

        config = self.schema.validate(config_dict)
        names = set()

        # Ensure the uniqueness of the model's name.
        for m in config["models"]:
            if m["name"] in names:
                raise DuplicateNameError(m["name"])
            names.add(m["name"])
        return config


def load(plugins):
    """Code surgar to load the server's configuration."""
    return Config(plugins).load()
