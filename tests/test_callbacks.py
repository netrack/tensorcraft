import tensorflow as tf
import numpy as np
import unittest

from tensorcraft import callbacks
from tests import asynctest
from tests import clienttest
from tests import kerastest


class TestCallbacks(asynctest.AsyncTestCase):

    @clienttest.unittest_mock_client("push")
    def test_on_epoch_end(self, push_mock):
        cb = callbacks.ModelCheckpoint(verbose=1)

        model = tf.keras.models.Sequential()
        model.add(tf.keras.layers.Activation("tanh"))
        model.compile(optimizer="sgd", loss="binary_crossentropy")

        x, y = np.array([[1.0]]), np.array([[1.0]])
        model.fit(x, y, callbacks=[cb], epochs=3)

        push_mock.assert_called()


if __name__ == "__main__":
    unittest.main()
