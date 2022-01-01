import logging
import asyncio

from . import UPNPFinder, UPNPDevice


def on_device(device: UPNPDevice):
    pass


async def main():
    async with UPNPFinder() as finder:
        logging.info("Started")
        async for device in finder.find_devices(3):
            name = device.get("device.friendlyName")
            service_list = device.get("device.serviceList")
            services = {}
            if service_list is not None:
                for _, service in service_list.items():
                    service_name = service["serviceId"].split(':')[-1]
                    services[service_name] = service
            print(name)
            print(service_list)
            print("")


def cli():
    asyncio.run(main())
