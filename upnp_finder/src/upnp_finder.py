import logging
import socket
from typing import Any, Awaitable, Callable, List, Optional, Tuple

from tornado.concurrent import Future
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop

from .upnp_device import UPNPDevice


def expect(value: Optional[Any], message: str) -> Any:
    if value is None:
        raise RuntimeError(message)
    return value


def _nop(_: UPNPDevice) -> None:
    pass


class UPNPFinder:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._tracked: List[str] = []
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

    @property
    def tracked(self) -> List[str]:
        # return a copy
        return list(self._tracked)

    def setup(
        self,
        callback: Callable[[UPNPDevice], None]
    ) -> Tuple[socket.socket, Callable[[int, int], None]]:
        self.sock.settimeout(5.0)
        self.callback = callback
        return (self.sock, self._handle_response)

    def send_probe(self):
        logging.info("Discovering devices...")
        self.sock.sendto(self.mcast_msg, self.mcast_addr)

    def send_probe_with_delay(self, delay: float) -> Awaitable[bool]:
        """Send an SSDP probe and wait `delay` seconds"""
        fut = Future()
        self.send_probe()
        IOLoop.current().call_later(delay, lambda: fut.set_result(True))
        return fut

    async def make_device(self, location: str):
        try:
            http_client = AsyncHTTPClient()
            response = await http_client.fetch(location)
            self._tracked.append(location)
            device = UPNPDevice(location, response.body.decode("utf-8"))
            self.callback(device)
        except Exception as e:
            logging.error("upnpfinder->make_device")
            logging.error(f"Location: {location}")
            logging.error(e)

    def untrack(self, url: str) -> bool:
        if url in self._tracked:
            self._tracked.remove(url)
            return True
        return False

    def _handle_response(self, fd: int, events: int):
        try:
            res, _ = self.sock.recvfrom(400)
            res = res.decode("ascii")
            res = res[res.find('\r\n') + 2:]
            headers = HTTPHeaders.parse(res)
            location: str = expect(
                headers.get("location"),
                "BUG: expected location header"
            )
            if location not in self._tracked:
                logging.info("Device found!")
                IOLoop.current().add_callback(self.make_device, location)
        except Exception as e:
            logging.error(f"upnpfinder->find_devices\n{e}")
