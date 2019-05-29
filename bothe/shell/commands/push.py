from bothe.shell import app


class Push(app.Command):
    name = "push"
    aliases = ["p"]
    help = "push model"
    arguments = [
        (["path"],
         dict(metavar="PATH",
              help="model location"))]
