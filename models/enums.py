from __future__ import annotations

from enum import Enum, auto


class ItemType(Enum):
    FILE = auto()
    DIRECTORY = auto()
