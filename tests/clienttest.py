import unittest.mock

from tensorcraft.client import Model
from tests import asynctest


def unittest_mock_model_client(method: str):
    return unittest.mock.patch.object(Model, method,
                                      new_callable=asynctest.AsyncMagicMock)
