import re
import socket
from asyncio.futures import Future
from unittest.mock import MagicMock

import httpx
import pytest
import upnp_finder.src.upnp_finder as upnp_finder
from upnp_finder import UPNPFinder


class MockResponse(httpx.Response):
    def raise_for_status(self) -> None:
        pass

    @property
    def text(self):
        return re.sub(r"\r*\n\s*", "", """
<?xml version="1.0"?>
<root xmlns="urn:Belkin:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>My Test Device</deviceType>
    <friendlyName>TEST</friendlyName>
    <presentationURL>/test.html</presentationURL>
</device>
</root>
""")


@pytest.mark.asyncio
async def test_send_probe():

    class MockSock(socket.socket):
        pass

    sock = MockSock()
    sock.sendto = MagicMock()
    finder = UPNPFinder()
    expected_args = (finder.mcast_msg, finder.mcast_addr)
    finder.sock = sock
    finder.send_probe()
    assert sock.sendto.call_count == 1
    assert sock.sendto.call_args[0] == expected_args


@pytest.mark.asyncio
async def test_make_device():
    finder = UPNPFinder()
    fut = Future()
    upnp_finder.httpx.AsyncClient.get = MagicMock(return_value=fut)
    fut.set_result(MockResponse(200))
    await finder.make_device("TEST_URL")
    finder.send_probe()
    the_device = await finder._device_buffer.get()
    assert the_device is not None
    assert the_device.get("device.friendlyName") == "TEST"
    assert the_device.get("device.deviceType") == "My Test Device"
    assert len(finder.tracked) == 1
    assert finder.untrack("TEST_URL")

# TO BE CONTINUED
