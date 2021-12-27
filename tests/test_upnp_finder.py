import re
import socket
from asyncio.futures import Future
from unittest.mock import MagicMock

import httpx
import pytest
import upnp_finder.src.upnp_finder as upnp_finder
from upnp_finder import UPNPFinder
from upnp_finder.src.upnp_device import UPNPDevice


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
    from datetime import datetime

    class MockSock(socket.socket):
        pass

    epsilon = 0.1  # Just check for correct time dimension, not high accuracy
    expected_delay = 1
    sock = MockSock()
    sock.sendto = MagicMock()
    finder = UPNPFinder()
    expected_args = (finder.mcast_msg, finder.mcast_addr)
    finder.sock = sock
    start = datetime.now()
    await finder.send_probe_with_delay(expected_delay)
    actual_delay = (datetime.now() - start).seconds

    assert (
        (expected_delay - epsilon) < actual_delay and
        actual_delay < (expected_delay + epsilon)
    )
    assert sock.sendto.call_count == 1
    assert sock.sendto.call_args[0] == expected_args


@pytest.mark.asyncio
async def test_make_device():
    device_fut = Future()
    finder = UPNPFinder()
    finder.callback = lambda d: device_fut.set_result(d)
    fut = Future()
    upnp_finder.httpx.AsyncClient.get = MagicMock(return_value=fut)
    fut.set_result(MockResponse(200))
    await finder.make_device("TEST_URL")
    the_device: UPNPDevice = await device_fut
    assert the_device is not None
    assert the_device.get("device.friendlyName") == "TEST"
    assert the_device.get("device.deviceType") == "My Test Device"
    assert len(finder.tracked) == 1
    assert finder.untrack("TEST_URL")

# TO BE CONTINUED
