import argparse
import sys

import knuckle
import knuckle.shell.commands


class App:

    def __init__(self, prog, modules):
        self.parser = argparse.ArgumentParser(
            prog=prog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        self.parser.set_defaults(func=lambda *x: self.parser.print_help())
        subparsers = self.parser.add_subparsers()

        self.modules = [m(subparsers) for m in modules]

    def argument(self, args, kwargs):
        self.parser.add_argument(*args, **kwargs)

    def start(self):
        args = self.parser.parse_args()
        return args.func(args=args)


def main():
    a = App(prog="knuckle", modules=[knuckle.shell.commands.Server,
                                     knuckle.shell.commands.Push,
                                     knuckle.shell.commands.Remove,
                                     knuckle.shell.commands.List])

    a.argument(["-s", "--service-url"],
               dict(help="service endpoint",
                    default="http://localhost:5678"))

    a.argument(["-v", "--version"],
               dict(help="print version and exit",
                    action="version",
                    version="%(prog)s {0}".format(knuckle.__version__)))

    sys.exit(a.start().value)


if __name__ == "__main__":
    main()