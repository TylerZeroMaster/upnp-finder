import asyncio
import logging
import socket
from typing import (AsyncGenerator, Awaitable, List, Mapping,
                    Optional, TypeVar)

import httpx

from .upnp_device import UPNPDevice

T = TypeVar("T")


def expect(value: Optional[T], message: str) -> T:
    if value is None:
        raise RuntimeError(message)
    return value


def _parse_headers(header_str: str) -> Mapping[str, str]:
    headers: Mapping[str, str] = {}
    prev_key: Optional[str] = None
    for line in header_str.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if line:
            if line[0].isspace():
                if prev_key is None:
                    raise ValueError("First header cannot start with space")
                else:
                    headers[prev_key] += " " + line.lstrip()
            else:
                idx = line.find(":")
                if idx == -1:
                    break
                prev_key = line[:idx].lower()
                value = line[idx+1:]
                headers[prev_key] = value.strip()
    return headers


class UPNPFinder:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5.0)
        self._tracked: List[str] = []
        self._http_client = httpx.AsyncClient()
        self.mcast_addr = ("239.255.255.250", 1900)
        self.mcast_msg = "\r\n".join((
            "M-SEARCH * HTTP/1.1",
            "HOST:239.255.255.250:1900",
            "ST:upnp:rootdevice",
            "MX:2",
            'MAN:"ssdp:discover"',
            "", ""
        )).encode("ascii")
        self._device_buffer: asyncio.Queue[UPNPDevice] = asyncio.Queue()
        asyncio.get_running_loop().add_reader(self.sock, self._handle_response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()

    @property
    def tracked(self) -> List[str]:
        # return a copy
        return list(self._tracked)

    async def find_devices(
        self,
        timeout: float
    ) -> AsyncGenerator[UPNPDevice, None]:
        try:
            self.send_probe()
            while True:
                yield await asyncio.wait_for(
                    self._device_buffer.get(),
                    timeout
                )
                self._device_buffer.task_done()
        except asyncio.exceptions.TimeoutError:
            pass

    def send_probe(self):
        logging.info("Discovering devices...")
        self.sock.sendto(self.mcast_msg, self.mcast_addr)

    def send_probe_with_delay(self, delay: float) -> Awaitable[bool]:
        """Send an SSDP probe and wait `delay` seconds"""
        fut = asyncio.futures.Future()
        self.send_probe()
        asyncio.get_running_loop().call_later(
            delay,
            lambda: fut.set_result(True)
        )
        return fut

    async def make_device(self, location: str):
        try:
            response = await self._http_client.get(location)
            response.raise_for_status()
            device = UPNPDevice(location, response.text)
            self._tracked.append(location)
            self._device_buffer.put_nowait(device)
        except Exception as e:
            logging.error("upnpfinder->make_device")
            logging.error(f"Location: {location}")
            logging.error(e)

    def untrack(self, url: str) -> bool:
        if url in self._tracked:
            self._tracked.remove(url)
            return True
        return False

    async def close(self):
        await self._http_client.aclose()

    def _handle_response(self):
        try:
            res, _ = self.sock.recvfrom(400)
            res = res.decode("ascii")
            res = res[res.find("\r\n") + 2:]
            headers = _parse_headers(res)
            location = expect(
                headers.get("location"),
                "BUG: expected location header"
            )
            if location not in self._tracked:
                logging.info("Device found!")
                asyncio.get_running_loop().create_task(
                    self.make_device(location)
                )
        except Exception as e:
            logging.error(f"upnpfinder->find_devices\n{e}")
