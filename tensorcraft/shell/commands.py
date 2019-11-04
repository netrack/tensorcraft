import aiofiles
import argparse
import flagparse
import importlib
import pathlib
import tarfile
import yaml

import tensorcraft.errors

from tensorcraft import asynclib
from tensorcraft import client
from tensorcraft.shell import termlib


class AsyncSubCommand(flagparse.SubCommand):

    async def async_handle(self, args: flagparse.Namespace) -> None:
        pass

    def handle(self, args: flagparse.Namespace) -> None:
        asynclib.run(self.async_handle(args))


class Server(flagparse.SubCommand):
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

    def handle(self, args: flagparse.Namespace) -> None:
        try:
            server = importlib.import_module("tensorcraft.server")
            server.Server.start(**args.__dict__)
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to start server. {e}.")


class Push(AsyncSubCommand):
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

    async def async_handle(self, args: flagparse.Namespace) -> None:
        print(f"loading model {args.name}:{args.tag}")

        try:
            if not args.path.exists():
                raise ValueError(f"{args.path} does not exist")
            if not tarfile.is_tarfile(str(args.path)):
                raise ValueError(f"{args.path} is not a tar file")

            asyncreader = asynclib.reader(args.path)
            reader = termlib.async_progress(args.path, asyncreader)

            async with client.Model.new(**args.__dict__) as models:
                await models.push(args.name, args.tag, reader)
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to push model. {e}")


class Remove(AsyncSubCommand):
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

    async def async_handle(self, args: flagparse.Namespace) -> None:
        try:
            async with client.Model.new(**args.__dict__) as models:
                await models.remove(args.name, args.tag)
        except tensorcraft.errors.NotFoundError as e:
            if not args.quiet:
                raise flagparse.ExitError(1, f"{e}")
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to remove model. {e}.")


class List(AsyncSubCommand):
    """Shell command to list models from the server."""

    name = "list"
    aliases = ["ls"]
    help = "list models"

    description = "List available models."

    arguments = []

    async def async_handle(self, args: flagparse.Namespace) -> None:
        try:
            async with client.Model.new(**args.__dict__) as models:
                for model in await models.list():
                    print("{name}:{tag}".format(**model))
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to list models. {e}.")


class Export(AsyncSubCommand):
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

    async def async_handle(self, args: flagparse.Namespace) -> None:
        try:
            async with aiofiles.open(args.path, "wb+") as writer:
                async with client.Model.new(**args.__dict__) as models:
                    await models.export(args.name, args.tag, writer)
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to export model. {e}")


class Status(AsyncSubCommand):
    """Shell command to retrieve server status information."""

    name = "status"
    aliases = []
    help = "server status"

    description = "Retrieve server status."""

    arguments = []

    async def async_handle(self, args: flagparse.Namespace) -> None:
        try:
            async with client.Model.new(**args.__dict__) as models:
                status = await models.status()
                print(yaml.dump(status), end="")
        except Exception as e:
            raise flagparse.ExitError(1, f"Failed to export model. {e}")
