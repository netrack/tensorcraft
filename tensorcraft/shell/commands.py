import aiofiles
import argparse
import enum
import importlib
import pathlib
import tarfile
import yaml

import tensorcraft.errors

from tensorcraft import asynclib
from tensorcraft.client import Client
from tensorcraft.shell import termlib


class ExitStatus(enum.Enum):
    Success = 0
    Failure = 1


class Formatter(argparse.ArgumentDefaultsHelpFormatter):
    """Format arguments with default values for wide screens.

    Print the usage of the commands to the 140 character terminals.
    """

    def __init__(self, prog, indent_increment=2, max_help_position=48,
                 width=140):
        super().__init__(prog, indent_increment, max_help_position, width)


class Command:
    """Shell sub-command."""

    __attributes__ = [
        "name",
        "aliases",
        "arguments",
        "help",
        "description",
    ]

    def __init__(self, subparsers):
        # Copy all meta parameters of the command into the __meta__ dictionary,
        # so it can be accessible during the setup of commands.
        attrs = {attr: getattr(self, attr, None)
                 for attr in self.__attributes__}

        self.__meta__ = argparse.Namespace(**attrs)
        self.subcommands = {}

        self.subparser = subparsers.add_parser(
            name=self.__meta__.name,
            help=self.__meta__.help,
            aliases=(self.__meta__.aliases or []),
            description=self.__meta__.description,
            formatter_class=Formatter)

        for args, kwargs in self.__meta__.arguments or []:
            self.subparser.add_argument(*args, **kwargs)

        # At least print the help message for the command.
        self.subparser.set_defaults(func=self.handle)

        # Search for sub-classes that represent sub-commands.
        class_dict = self.__class__.__dict__

        subcommands = filter(lambda o: isinstance(o, type),
                             class_dict.values())

        subcommands = list(subcommands)
        if not subcommands:
            return

        subparsers = self.subparser.add_subparsers(dest=self.__meta__.name)
        for command_class in subcommands:
            command = command_class(subparsers)
            self.subcommands[command_class.__name__] = command

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        self.subparser.print_help()
        return ExitStatus.Success


class Server(Command):
    """Server shell command used to run a server."""

    name = "server"
    aliases = ["s"]
    help = "run server"

    description = "Start serving models."

    arguments = [
        (["-H", "--host"],
         dict(metavar="HOST",
              help="address to listen to",
              default="localhost")),
        (["-p", "--port"],
         dict(metavar="PORT",
              help="port to listen to",
              default="5678")),
        (["--data-root"],
         dict(metavar="PATH",
              help="root directory of persistent state",
              default="/var/lib/tensorcraft")),
        (["--pidfile"],
         dict(metavar="PIDFILE",
              help="path to use for daemon pid file",
              default="/var/run/tensorcraft.pid")),
        (["--strategy"],
         dict(metavar="STRATEGY",
              choices=["mirrored", "multi_worker_mirrored", "no"],
              default="mirrored",
              help="model execution strategy")),
        (["--preload"],
         dict(action="store_true",
              default=False,
              help="preload all models into the memory before start"))]

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        try:
            server = importlib.import_module("tensorcraft.server")
            server.Server.start(**args.__dict__)
        except Exception as e:
            print(f"Failed to start server. {e}.")
            return ExitStatus.Failure
        return ExitStatus.Success


class Push(Command):
    """Shell command to push model to the server."""

    name = "push"
    aliases = ["p"]
    help = "push model"

    description = "Push a model image to the repository."

    arguments = [
        (["-n", "--name"],
         dict(metavar="NAME",
              type=str,
              required=True,
              default=argparse.SUPPRESS,
              help="model name")),
        (["-t", "--tag"],
         dict(metavar="TAG",
              type=str,
              required=True,
              default=argparse.SUPPRESS,
              help="model tag")),
        (["path"],
         dict(metavar="PATH",
              type=pathlib.Path,
              default=argparse.SUPPRESS,
              help="model location"))]

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        print(f"loading model {args.name}:{args.tag}")

        try:
            if not args.path.exists():
                raise ValueError(f"{args.path} does not exist")
            if not tarfile.is_tarfile(str(args.path)):
                raise ValueError(f"{args.path} is not a tar file")

            client = Client.new(**args.__dict__)

            asyncreader = asynclib.reader(args.path)
            reader = termlib.async_progress(args.path, asyncreader)
            coro = client.push(args.name, args.tag, reader)

            asynclib.run(coro)
        except Exception as e:
            print(f"Failed to push model. {e}")
            return ExitStatus.Failure
        return ExitStatus.Success


class Remove(Command):
    """Shell command to remove the model from server."""

    name = "remove"
    aliases = ["rm"]
    help = "remove model"

    description = "Remove a model from the repository."

    arguments = [
        (["-n", "--name"],
         dict(metavar="NAME",
              type=str,
              help="model name")),
        (["-q", "--quiet"],
         dict(action="store_true",
              help="do not return error on missing model")),
        (["-t", "--tag"],
         dict(metavar="TAG",
              type=str,
              help="model tag"))]

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        client = Client.new(**args.__dict__)
        coro = client.remove(args.name, args.tag)

        try:
            asynclib.run(coro)
        except tensorcraft.errors.NotFoundError as e:
            if not args.quiet:
                print(f"{e}")
                return ExitStatus.Failure
        except Exception as e:
            print(f"Failed to remove model. {e}.")
            return ExitStatus.Failure
        return ExitStatus.Success


class List(Command):
    """Shell command to list models from the server."""

    name = "list"
    aliases = ["ls"]
    help = "list models"

    description = "List available models."

    arguments = []

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        client = Client.new(**args.__dict__)
        coro = client.list()

        try:
            for model in asynclib.run(coro):
                print("{name}:{tag}".format(**model))
        except Exception as e:
            print(f"Failed to list models. {e}.")
            return ExitStatus.Failure
        return ExitStatus.Success


class Export(Command):
    """Shell command to export model from the server."""

    name = "export"
    aliases = []
    help = "export model tar"

    description = "Export model as TAR."

    arguments = [
        (["-n", "--name"],
         dict(metavar="NAME",
              type=str,
              required=True,
              default=argparse.SUPPRESS,
              help="model name")),
        (["-t", "--tag"],
         dict(metavar="TAG",
              type=str,
              required=True,
              default=argparse.SUPPRESS,
              help="model tag")),
        (["path"],
         dict(metavar="PATH",
              type=pathlib.Path,
              default=argparse.SUPPRESS,
              help="file location"))]

    async def _handle(self, args: argparse.Namespace) -> ExitStatus:
        async with aiofiles.open(args.path, "wb+") as writer:
            client = Client.new(**args.__dict__)
            await client.export(args.name, args.tag, writer)

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        try:
            asynclib.run(self._handle(args))
        except Exception as e:
            print(f"Failed to export model. {e}")
            return ExitStatus.Failure
        return ExitStatus.Success


class Status(Command):
    """Shell command to retrieve server status information."""

    name = "status"
    aliases = []
    help = "server status"

    description = "Retrieve server status."""

    arguments = []

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        client = Client.new(**args.__dict__)
        coro = client.status()

        try:
            status = asynclib.run(coro)
            print(yaml.dump(status), end="")
        except Exception as e:
            print(f"Failed to export model. {e}")
            return ExitStatus.Failure
        return ExitStatus.Success
