import logging
import asyncio

from . import UPNPFinder, UPNPDevice


def on_device(device: UPNPDevice):
    pass


async def main():
    async with UPNPFinder() as finder:
        # finder.setup(on_device)
        logging.info("Started")
        async for device in finder.find_devices(3):
            print(device.get("device.friendlyName"))


def cli():
    asyncio.run(main())
