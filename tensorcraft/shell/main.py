import argparse
import sys

import tensorcraft

from tensorcraft.shell import commands


class App:

    arguments = [
        (["-s", "--service-url"],
         dict(help="service endpoint",
              default="http://localhost:5678")),
        (["--tls"],
         dict(action="store_true",
              default=False,
              help="use TLS")),
        (["--tlsverify"],
         dict(action="store_true",
              default=False,
              help="use TLS and verify remove")),
        (["--tlscacert"],
         dict(metavar="TLS_CACERT",
              default=tensorcraft.homepath.joinpath("cacert.pem"),
              help="trust certs signed only by this CA")),
        (["--tlscert"],
         dict(metavar="TLS_CERT",
              default=tensorcraft.homepath.joinpath("cert.pem"),
              help="path to TLS certificate file")),
        (["--tlskey"],
         dict(metavar="TLS_KEY",
              default=tensorcraft.homepath.joinpath("key.pem"),
              help="path to TLS key fine")),
        (["-v", "--version"],
         dict(help="print version and exit",
              action="version",
              version="%(prog)s {0}".format(tensorcraft.__version__)))]

    def __init__(self, prog, modules):
        self.parser = argparse.ArgumentParser(
            prog=prog, formatter_class=commands.Formatter)

        self.parser.set_defaults(func=self.handle)

        for args, kwargs in self.arguments:
            self.parser.add_argument(*args, **kwargs)

        subparsers = self.parser.add_subparsers()
        self.modules = [m(subparsers) for m in modules]

    def handle(self, args: argparse.Namespace) -> commands.ExitStatus:
        self.parser.print_help()
        return commands.ExitStatus.Failure

    def start(self):
        args = self.parser.parse_args()
        return args.func(args=args)


def main():
    a = App(prog="tensorcraft",
            modules=[commands.Server,
                     commands.Push,
                     commands.Remove,
                     commands.List,
                     commands.Export,
                     commands.Status])

    sys.exit(a.start().value)


if __name__ == "__main__":
    main()
