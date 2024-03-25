from dataclasses import dataclass
import datetime
from typing import Any


@dataclass
class Event:
    source: str
    timestamp: datetime.datetime
    value: Any
