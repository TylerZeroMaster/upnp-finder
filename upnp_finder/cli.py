import logging

from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.web import Application

from .src.upnp_finder import UPNPFinder


def on_device(device):
    print("Name: ", device.get("device.friendlyName"))
    print("MAC: ", device.get("device.macAddress"))


class TestServer(Application):
    def start(self):
        timeout = 15
        upnpfinder = UPNPFinder()
        self.discovery_loop = PeriodicCallback(
            upnpfinder.send_probe,
            timeout * 1000
        )
        sock, callback = upnpfinder.setup(on_device)
        # ignore this type error: just pylance failing to account for overloads
        IOLoop.current().add_handler(sock, callback, IOLoop.READ)
        logging.info("Started!")
        upnpfinder.send_probe()
        self.discovery_loop.start()
        logging.info(f"Discovering devices every {timeout} seconds...")


def cli():
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Starting server...")
    app = TestServer()
    app.start()
    app.listen(8990)
    IOLoop.current().start()


if __name__ == "__main__":
    cli()
