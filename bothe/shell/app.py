import argparse


class App:

    def __init__(self, prog, modules):
        self.parser = argparse.ArgumentParser(
            prog=prog, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        self.parser.set_defaults(func=lambda *x: self.parser.print_help())
        subparsers = self.parser.add_subparsers()

        self.modules = [m(subparsers) for m in modules]

    def argument(self, args, kwargs):
        self.parser.add_argument(*args, **kwargs)

    def start(self):
        args = self.parser.parse_args()
        args.func(argparse.Namespace(args=args))
