import bothe.config
import bothe.plugin
import bothe.web.server


class Server:

    def __init__(self, plugins):
        super().__init__()
        self.plugins = plugins
        self.models = {}

    def _plugin_name(self, model_config):
        """Get plugin name from the model configuration."""
        del model_config["name"]
        keys = set(model_config.keys())
        return keys.pop() if keys else ""

    def serve(self):
        config = bothe.config.load(self.plugins)

        for model_config in config["models"]:
            name = model_config["name"]
            plugin_name = self._plugin_name(model_config)
            print(plugin_name)

            if plugin_name not in self.plugins:
                # TODO: think about what to do with this.
                continue

            plugin = self.plugins[plugin_name]()
            plugin.compile(model_config[plugin_name])

            self.models[name] = plugin

        s = bothe.web.server.Server()
        for name, model in self.models.items():
            s.handle(name, model)

        s.serve()


def serve(plugins):
    Server(plugins).serve()


if __name__ == "__main__":
    serve(bothe.plugin.ALL)
