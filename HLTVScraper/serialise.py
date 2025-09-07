# serialize_encoder.py
from dataclasses import is_dataclass, asdict
from enum import Enum
import json

class DataclassEnumEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)           # recurses into nested dataclasses
        if isinstance(o, Enum):
            return o.value             # IntEnum -> int; Enum -> str
        return super().default(o)
