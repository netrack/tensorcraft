import argparse
import pathlib
import tarfile
import tempfile
import unittest
import unittest.mock

from polynome import client
from polynome import errors
from polynome.shell import commands
from tests import cryptotest
from tests import kerastest
from tests import asynctest


def unittest_mock_client(method: str):
    return unittest.mock.patch.object(client.Client, method,
                                      new_callable=asynctest.AsyncMagicMock)


class TestCommand(unittest.TestCase):

    def run_command(self, command_class: type, args: argparse.Namespace
                    ) -> commands.ExitStatus:
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        return command_class(subparsers).handle(args)

    @unittest_mock_client("list")
    @unittest.mock.patch("builtins.print")
    def test_list(self, print_mock, list_mock):
        m = kerastest.new_model()
        list_mock.return_value = [m.to_dict()]

        args = argparse.Namespace()
        exit_status = self.run_command(commands.List, args)

        print_mock.assert_called_with(str(m))
        self.assertEqual(commands.ExitStatus.Success, exit_status)

    @unittest_mock_client("remove")
    def test_remove(self, remove_mock):
        m = kerastest.new_model()

        args = argparse.Namespace(name=m.name, tag=m.tag)
        exit_status = self.run_command(commands.Remove, args)

        remove_mock.assert_called_with(m.name, m.tag)
        self.assertEqual(commands.ExitStatus.Success, exit_status)

    @unittest_mock_client("remove")
    def test_remove_not_found(self, remove_mock):
        m = kerastest.new_model()
        remove_mock.side_effect = errors.NotFoundError(m.name, m.tag)

        args = argparse.Namespace(name=m.name, tag=m.tag, quiet=False)
        exit_status = self.run_command(commands.Remove, args)

        remove_mock.assert_called_with(m.name, m.tag)
        self.assertEqual(commands.ExitStatus.Failure, exit_status)

    @unittest_mock_client("remove")
    def test_remove_not_found_quiet(self, remove_mock):
        m = kerastest.new_model()
        remove_mock.side_effect = errors.NotFoundError(m.name, m.tag)

        args = argparse.Namespace(name=m.name, tag=m.tag, quiet=True)
        exit_status = self.run_command(commands.Remove, args)

        remove_mock.assert_called_with(m.name, m.tag)
        self.assertEqual(commands.ExitStatus.Success, exit_status)

    @unittest_mock_client("push")
    def test_push(self, push_mock):
        with tempfile.NamedTemporaryFile() as tf:
            with tarfile.open(tf.name, mode="w") as tar:
                tar.add("tests", arcname="")

            m = kerastest.new_model()
            path = pathlib.Path(tf.name)

            args = argparse.Namespace(name=m.name, tag=m.tag, path=path)
            exit_status = self.run_command(commands.Push, args)

            self.assertEqual(commands.ExitStatus.Success, exit_status)

    @unittest_mock_client("push")
    def test_push_file_not_exists(self, push_mock):
        m = kerastest.new_model()
        path = pathlib.Path(cryptotest.random_string())

        args = argparse.Namespace(name=m.name, tag=m.tag, path=path)
        exit_status = self.run_command(commands.Push, args)

        self.assertEqual(commands.ExitStatus.Failure, exit_status)

    @unittest_mock_client("export")
    def test_export(self, export_mock):
        with tempfile.NamedTemporaryFile() as tf:
            m = kerastest.new_model()
            path = pathlib.Path(tf.name)

            args = argparse.Namespace(name=m.name, tag=m.tag, path=path)
            exit_status = self.run_command(commands.Export, args)

            self.assertEqual(commands.ExitStatus.Success, exit_status)


if __name__ == "__main__":
    unittest.main()
