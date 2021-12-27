import logging
import asyncio

from . import UPNPFinder, UPNPDevice


def on_device(device: UPNPDevice):
    print("Name: ", device.get("device.friendlyName"))
    print("MAC: ", device.get("device.macAddress"))


async def main():
    async with UPNPFinder() as finder:
        finder.setup(on_device)
        logging.info("Started")
        await finder.send_probe_with_delay(5)


def cli():
    asyncio.run(main())
