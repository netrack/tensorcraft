import argparse
import enum
import pathlib

import bothe.asynclib
import bothe.client
import bothe.model


class ExitStatus(enum.Enum):
    Success = 0
    Failure = 1


class Command:
    """Shell sub-command."""

    __attributes__ = [
        "name",
        "aliases",
        "arguments",
        "help",
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
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        for args, kwargs in self.__meta__.arguments or []:
            self.subparser.add_argument(*args, **kwargs)

        # At least print the help message for the command.
        self.subparser.set_defaults(func=self.handle)

        # Search for sub-classes that represent sub-commands.
        class_dict = self.__class__.__dict__
        filter_predicate = lambda o: isinstance(o, type)

        subcommands = filter(filter_predicate, class_dict.values())
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
              default=".var/lib/bothe")),
        (["--strategy"],
         dict(metavar="STRATEGY",
              help="model execution strategy"))]

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        import bothe.server
        s = bothe.server.Server(args)
        s.serve()
        return ExitStatus.Success


class Push(Command):
    """Shell command to push model to the server."""

    name = "push"
    aliases = ["p"]
    help = "push model"

    arguments = [
        (["-n", "--name"],
         dict(metavar="NAME",
              type=str,
              help="model name")),
        (["-t", "--tag"],
         dict(metavar="TAG",
              type=str,
              default="latest",
              help="model tag")),
        (["path"],
         dict(metavar="PATH",
              type=str,
              help="model location"))]

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        print("loading model {0}:{1}".format(args.name, args.tag))
        client = bothe.client.Client(service_url=args.service_url)

        path = pathlib.Path(args.path)
        task = client.push(args.name, args.tag, path)

        try:
            bothe.asynclib.run(task)
        except Exception as e:
            print("Failed to push model. {0}".format(e))
            return ExitStatus.Failure
        return ExitStatus.Success


class Remove(Command):
    """Shell command to remove the model from server."""

    name = "remove"
    aliases = ["rm"]
    help = "remove model"

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
        client = bothe.client.Client(service_url=args.service_url)
        task = client.remove(args.name, args.tag)

        try:
            bothe.asynclib.run(task)
        except bothe.model.NotFoundError as e:
            if not args.quiet:
                print("{0}.".format(e))
                return ExitStatus.Failure
        except Exception as e:
            print("Failed to remove model. {0}.".format(e))
            return ExitStatus.Failure
        return ExitStatus.Success


class List(Command):
    """Shell command to list models from the server."""

    name = "list"
    aliases = ["ls"]
    help = "list models"

    arguments = []

    def handle(self, args: argparse.Namespace) -> ExitStatus:
        client = bothe.client.Client(service_url=args.service_url)
        task = client.list()

        try:
            for model in bothe.asynclib.run(task):
                print("{name}:{tag}".format(**model))
        except Exception as e:
            print("Failed to list models. {0}.".format(e))
            return ExitStatus.Failure
        return ExitStatus.Success
