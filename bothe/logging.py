import absl.logging
import logging
import os

# Disable logging from TensorFlow CPP files.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Disable asyncio and TensorFlow logging.
logging.getLogger("asyncio").disabled = True
logging.getLogger("tensorflow").disabled = True

for h in logging.root.handlers:
    logging.root.removeHandler(h)


logging.basicConfig(level=logging.NOTSET, format="%(message)s")
logger = logging.getLogger("bothe")


debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical
