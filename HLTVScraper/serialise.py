# serialize_encoder.py
from dataclasses import is_dataclass, asdict
from enum import Enum
from datetime import datetime, date
import json

class DataclassEnumEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)           # recurses into nested dataclasses
        if isinstance(o, Enum):
            return o.value             # IntEnum -> int; Enum -> str
        if isinstance(o, (datetime, date)):
            return o.isoformat()  # UTC ISO 8601 string
        return super().default(o)
