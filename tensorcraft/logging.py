import importlib
import logging
import os


# Disable logging from TensorFlow CPP files.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Disable asyncio and TensorFlow logging.
logging.getLogger("asyncio").disabled = True
logging.getLogger("tensorflow").disabled = True


try:
    # This import is done in a hope that TensorFlow will drop this
    # dependency in the future versions.
    absl_logging = importlib.import_module("absl.logging")

    # ABSL logging removes all root handlers and puts itself to the list of
    # root handlers, this dependency comes with TensorFlow, and we want to
    # modify this behaviour to make logs pretty and consistent.
    for h in logging.root.handlers:
        if isinstance(h, absl_logging.ABSLHandler):
            logging.root.removeHandler(h)
except ModuleNotFoundError:
    pass
    # Nothing to do.


internal_format = "{asctime} {levelname} - {message}"

internal_handler = logging.StreamHandler()
internal_handler.setFormatter(logging.Formatter(internal_format, style="{"))

internal_logger = logging.getLogger("tensorcraft")
internal_logger.addHandler(internal_handler)
internal_logger.setLevel(logging.DEBUG)
