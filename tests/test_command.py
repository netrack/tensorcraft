import argparse
import flagparse
import pathlib
import tarfile
import tempfile
import unittest
import unittest.mock

from tensorcraft import errors
from tensorcraft.shell import commands
from tests import clienttest
from tests import cryptotest
from tests import kerastest
from tests import asynctest



class TestCommand(unittest.TestCase):

    @clienttest.unittest_mock_model_client("list")
    @unittest.mock.patch("builtins.print")
    def test_list(self, print_mock, list_mock):
        m = kerastest.new_model()
        list_mock.return_value = [m.to_dict()]

        command = commands.List(unittest.mock.Mock())
        command.handle(flagparse.Namespace())
        print_mock.assert_called_with(str(m))

    @clienttest.unittest_mock_model_client("remove")
    def test_remove(self, remove_mock):
        m = kerastest.new_model()

        command = commands.Remove(unittest.mock.Mock())
        command.handle(flagparse.Namespace(name=m.name, tag=m.tag))
        remove_mock.assert_called_with(m.name, m.tag)

    @clienttest.unittest_mock_model_client("remove")
    def test_remove_not_found(self, remove_mock):
        m = kerastest.new_model()
        remove_mock.side_effect = errors.NotFoundError(m.name, m.tag)

        with self.assertRaises(flagparse.ExitError):
            args = flagparse.Namespace(name=m.name, tag=m.tag, quiet=False)
            command = commands.Remove(unittest.mock.Mock())
            command.handle(args)

        remove_mock.assert_called_with(m.name, m.tag)

    @clienttest.unittest_mock_model_client("remove")
    def test_remove_not_found_quiet(self, remove_mock):
        m = kerastest.new_model()
        remove_mock.side_effect = errors.NotFoundError(m.name, m.tag)

        command = commands.Remove(unittest.mock.Mock())
        command.handle(flagparse.Namespace(name=m.name, tag=m.tag, quiet=True))

        remove_mock.assert_called_with(m.name, m.tag)

    @clienttest.unittest_mock_model_client("push")
    def test_push(self, push_mock):
        with tempfile.NamedTemporaryFile() as tf:
            with tarfile.open(tf.name, mode="w") as tar:
                tar.add("tests", arcname="")

            m = kerastest.new_model()
            path = pathlib.Path(tf.name)

            args = flagparse.Namespace(name=m.name, tag=m.tag, path=path)
            command = commands.Push(unittest.mock.Mock())
            command.handle(args)

    @clienttest.unittest_mock_model_client("push")
    def test_push_file_not_exists(self, push_mock):
        m = kerastest.new_model()
        path = pathlib.Path(cryptotest.random_string())

        with self.assertRaises(flagparse.ExitError):
            args = flagparse.Namespace(name=m.name, tag=m.tag, path=path)
            command = commands.Push(unittest.mock.Mock())
            command.handle(args)


    @clienttest.unittest_mock_model_client("export")
    def test_export(self, export_mock):
        with tempfile.NamedTemporaryFile() as tf:
            m = kerastest.new_model()
            path = pathlib.Path(tf.name)

            args = flagparse.Namespace(name=m.name, tag=m.tag, path=path)
            command = commands.Export(unittest.mock.Mock())
            command.handle(args)


if __name__ == "__main__":
    unittest.main()
