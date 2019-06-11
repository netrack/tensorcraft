import absl.logging
import logging
import os

# Disable logging from TensorFlow CPP files.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Disable asyncio and TensorFlow logging.
logging.getLogger("asyncio").disabled = True
logging.getLogger("tensorflow").disabled = True

# ABSL logging removes all root handlers and puts itself to the list of
# root handlers, this dependency comes with TensorFlow, and we want to
# modify this behaviour to prettify logs.
for h in logging.root.handlers:
    logging.root.removeHandler(h)


internal_format = "{asctime} {levelname} - {message}"

internal_handler = logging.StreamHandler()
internal_handler.setFormatter(logging.Formatter(internal_format, style="{"))

internal_logger = logging.getLogger("bothe")
internal_logger.addHandler(internal_handler)
internal_logger.setLevel(logging.DEBUG)
