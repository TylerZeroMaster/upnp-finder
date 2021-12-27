# UPNP Finder

[![Tests](https://github.com/TylerZeroMaster/upnp-finder/workflows/tests/badge.svg)](https://github.com/TylerZeroMaster/upnp-finder/actions)

UPNP Finder helps you find UPNP devices on a network.

## Installation
```bash
poetry add "git+https://github.com/TylerZeroMaster/upnp-finder#<branch>"
```

# Usage
You can see a full example [here](./upnp_finder/cli.py).
```python
import asyncio

from upnp_finder import UPNPFinder, UPNPDevice


def device_callback(device: UPNPDevice):
    print("Got device!")


async def main():
    async with UPNPFinder() as finder:
        finder.setup(device_callback)
        # The 5 second delay gives devices time to respond
        await finder.send_probe_with_delay(5)


if __name__ == "__main__":
    asyncio.run(main())
```

# TODO
1. Either remove lxml or make better use of it
2. Maybe use an async queue instead of callbacks