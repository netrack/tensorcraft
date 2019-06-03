import argparse
import asyncio
import pathlib

import bothe.client


class Command:

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

    def handle(self, args):
        self.subparser.print_help()


class Server(Command):

    name = "server"
    aliases = ["s"]
    help = "run server"

    arguments = [
        (["-H", "--host"],
         dict(metavar="HOST",
              help="address to listen to",
              default="::")),
        (["--data-root"],
         dict(metavar="PATH",
              help="root directory of persistent state",
              default="/var/lib/bothe"))]

    def handle(self, args):
        s = bothe.server.Server(args)
        s.serve()


class Push(Command):

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
              help="model tag")),
        (["path"],
         dict(metavar="PATH",
              type=str,
              help="model location"))]

    def handle(self, args):
        client = bothe.client.Client()

        path = pathlib.Path(args.path)
        task = client.push(args.name, args.tag, path)
        asyncio.run(task)


class Remove(Command):

    name = "remove"
    aliases = ["rm"]
    help = "remove model"

    arguments = [
        (["-n", "--name"],
         dict(metavar="NAME",
              type=str,
              help="model name")),
        (["-t", "--tag"],
         dict(metavar="TAG",
              type=str,
              help="model tag"))]

    def handle(self, args):
        import bothe.server
        client = bothe.client.Client()

        task = client.remove(args.name, args.tag)
        asyncio.run(task)


class List(Command):

    name = "list"
    aliases = ["ls"]
    help = "list models"

    arguments = []

    def handle(self, args):
        client = bothe.client.Client()
        task = client.list()
        asyncio.run(task)
