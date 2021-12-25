from typing import Any, Optional


def expect(value: Optional[Any], message: str) -> Any:
    if value is None:
        raise RuntimeError(message)
    return value
