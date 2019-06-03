import bothe
import bothe.shell.app
import bothe.shell.commands




def main():
    #try:
        a = bothe.shell.app.App(prog="bothe", modules=[
            bothe.shell.commands.Server])

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
