import aiohttp

import bothe.config
import bothe.plugin
import bothe.plugin.error
import bothe.web.server


class Server:
    """Serve the models."""

    def __init__(self, plugins):
        self.plugins = plugins
        self.models = {}

    def _plugin_name(self, model_config):
        """Get plugin name from the model configuration."""
        del model_config["name"]
        keys = set(model_config.keys())
        return keys.pop() if keys else ""

    def _predict_handler(self, model):
        """Handle standard excetions of the model prediction.

        Translate standard plugin's exceptions in to the understandable HTTP
        status codes.
        """
        def _handler(obj):
            try:
                res = model.predict(obj)
            except bothe.plugin.error.InputShapeError as e:
                raise aiohttp.web.HTTPBadRequest(
                    content_type="text/plain", text=str(e))
            return res
        return _handler

    def serve(self):
        config = bothe.config.load(self.plugins)

        for model_config in config["models"]:
            name = model_config["name"]
            plugin_name = self._plugin_name(model_config)

            if plugin_name not in self.plugins:
                # TODO: think about what to do with this.
                continue

            plugin = self.plugins[plugin_name]()
            plugin.compile(model_config[plugin_name])

            self.models[name] = plugin

        s = bothe.web.server.Server()
        for name, model in self.models.items():
            s.handle(name, self._predict_handler(model))

        s.serve(host=config["server"]["host"],
                port=config["server"]["port"])


def serve(plugins):
    Server(plugins).serve()


if __name__ == "__main__":
    serve(bothe.plugin.ALL)
