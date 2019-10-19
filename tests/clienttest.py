import unittest.mock

from tensorcraft import client
from tests import asynctest


def unittest_mock_client(method: str):
    return unittest.mock.patch.object(client.Client, method,
                                      new_callable=asynctest.AsyncMagicMock)
