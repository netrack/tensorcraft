import bothe

from bothe.shell import app
from bothe.shell.commands import push



def main():
    #try:
        a = app.App(prog="bothe", modules=[push.Push])

        a.argument(["-s", "--service-url"],
            dict(help="service endpoint",
                 default="http://127.0.0.1:8080"))

        a.argument(["-v", "--version"],
            dict(help="print version and exit",
                 action="version",
                 version="%(prog)s {0}".format(bothe.__version__)))

        a.start()
    #except Exception as e:
    #    print(e)


if __name__ == "__main__":
    main()
