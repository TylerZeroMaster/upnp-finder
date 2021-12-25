import logging
import socket
from typing import Callable, List, Tuple

from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop

from .upnp_device import UPNPDevice
from .utils import expect


def _nop(_: UPNPDevice) -> None:
    pass


class UPNPFinder:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tracked: List[str] = []
        self.callback = _nop
        self.mcast_addr = ("239.255.255.250", 1900)
        self.mcast_msg = "\r\n".join((
            "M-SEARCH * HTTP/1.1",
            "HOST:239.255.255.250:1900",
            "ST:upnp:rootdevice",
            "MX:2",
            'MAN:"ssdp:discover"',
            "", ""
        )).encode("ascii")

    def setup(
        self,
        callback: Callable[[UPNPDevice], None]
    ) -> Tuple[socket.socket, Callable[[int, int], None]]:
        self.sock.settimeout(5.0)
        self.callback = callback
        return (self.sock, self.handle_response)

    def send_probe(self):
        logging.info("Discovering devices...")
        self.sock.sendto(self.mcast_msg, self.mcast_addr)

    async def make_device(self, location: str):
        try:
            http_client = AsyncHTTPClient()
            response = await http_client.fetch(location)
            self.tracked.append(location)
            device = UPNPDevice(location, response.body.decode("utf-8"))
            self.callback(device)
        except Exception as e:
            logging.error("upnpfinder->make_device")
            logging.error(f"Location: {location}")
            logging.error(e)

    def handle_response(self, fd: int, events: int):
        try:
            res, _ = self.sock.recvfrom(400)
            res = res.decode("ascii")
            res = res[res.find('\r\n') + 2:]
            headers = HTTPHeaders.parse(res)
            location: str = expect(
                headers.get("location"),
                "BUG: expected location header"
            )
            if location not in self.tracked:
                logging.info("Device found!")
                IOLoop.current().add_callback(self.make_device, location)
        except Exception as e:
            logging.error(f"upnpfinder->find_devices\n{e}")
