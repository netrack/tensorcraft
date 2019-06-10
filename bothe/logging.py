import logging
import os

# Disable logging from TensorFlow CPP files.
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Disable asyncio and TensorFlow logging.
logging.getLogger("asyncio").disabled = True
logging.getLogger("tensorflow").disabled = True

for h in logging.root.handlers:
    logging.root.removeHandler(h)


internal_logger = logging.getLogger("bothe")
