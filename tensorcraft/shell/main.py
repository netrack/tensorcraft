import flagparse
import sys

import tensorcraft

from tensorcraft.shell import commands


class Command(flagparse.Command):

    name = "tensorcraft"

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
              help="use TLS and verify remote")),
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
              help="path to TLS key file")),
        (["-v", "--version"],
         dict(help="print version and exit",
              action="version",
              version="%(prog)s {0}".format(tensorcraft.__version__)))]

    def handle(self, args: flagparse.Namespace) -> None:
        self.parser.print_help()


def main():
    Command([commands.Server,
             commands.Push,
             commands.Remove,
             commands.List,
             commands.Export,
             commands.Status]).parse()


if __name__ == "__main__":
    main()
