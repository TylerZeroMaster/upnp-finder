from typing import Any, Optional

import xmltodict


class UPNPDevice:
    def __init__(self, location: str, xmldoc: str):
        root = xmltodict.parse(xmldoc)
        if root is None:
            raise RuntimeError("Invalid xml document")
        # self._info = _parse_to_dict(root)
        self._info = root["root"]
        self.location = location
        presentationURL = self.get("device.presentationURL")
        if presentationURL is not None and presentationURL[0] == "/":
            self.set(
                "device.presentationURL",
                location[:location.rfind("/")] + presentationURL
            )

    def get(self, path: str) -> Optional[Any]:
        split_path = path.split(".")
        d = self._info
        for segment in split_path:
            if not isinstance(d, dict):
                return None
            d = d.get(segment, None)
            if d is None:
                break
        return d

    def set(self, path: str, value: Any):
        split_path = path.split(".")
        to_set = split_path[-1]
        d = self._info
        for segment in split_path[:-1]:
            if segment not in d:
                d[segment] = {}
            d = d[segment]
        d[to_set] = value
