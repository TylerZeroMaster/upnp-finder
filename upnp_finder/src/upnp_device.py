from typing import Any, Optional

from lxml import etree


def _parse_to_dict(tree: dict) -> dict:
    d = {}
    for i, child in enumerate(tree):
        key = tag = child.tag.split('}')[1] if '}' in child.tag else child.tag
        if key in d:
            key = "{}-{}".format(tag, i)
        if len(child):
            d[key] = _parse_to_dict(child)
        else:
            d[key] = child.text
    return d


class UPNPDevice:
    def __init__(self, location: str, xmldoc: str):
        root = etree.fromstring(xmldoc, None)
        self._info = _parse_to_dict(root)
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
