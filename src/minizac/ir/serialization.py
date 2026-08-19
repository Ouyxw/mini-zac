"""Helper functions for ZAIR JSON serialization and deserialization."""
import enum
import json
from dataclasses import fields, is_dataclass
from typing import Any

from ..architecture import RydbergSlot
from ..state import RydbergLocation, StorageLocation
from . import instruction as ins

# A map from the 'op' string to the corresponding instruction class
_OP_TO_CLASS: dict[str, type] = {
    "init": ins.Initialize,
    "1q_op": ins.OneQOp,
    "rearrange": ins.RearrangeJob,
    "rydberg_stage": ins.RydbergStageOp,
}

# A map from the 'kind' string to the corresponding location class
_KIND_TO_CLASS: dict[str, type] = {
    "storage": StorageLocation,
    "rydberg": RydbergLocation,
}

# A map to go from class back to the discriminator string
_CLASS_TO_DISCRIMINATOR: dict[type, str] = {
    **{v: k for k, v in _OP_TO_CLASS.items()},
    **{v: k for k, v in _KIND_TO_CLASS.items()},
}


def to_dict(obj: Any) -> Any:
    """
    Recursively convert a ZAIR object to a dictionary suitable for JSON.
    """
    if is_dataclass(obj):
        # Check if it's a discriminated union type
        discriminator = _CLASS_TO_DISCRIMINATOR.get(type(obj))
        d = {}
        if discriminator:
            if hasattr(obj, "op"):
                d["op"] = discriminator
            elif hasattr(obj, "kind"):
                d["kind"] = discriminator

        for f in fields(obj):
            if f.name in ("op", "kind") and f.init is False:
                continue
            value = to_dict(getattr(obj, f.name))
            d[f.name] = value
        return d
    
    if isinstance(obj, (list, tuple)):
        return type(obj)(to_dict(i) for i in obj)

    if isinstance(obj, enum.Enum):
        return obj.value

    return obj


def from_dict(data: Any) -> Any:
    """
    Recursively convert a dictionary (from JSON) to a ZAIR object.
    """
    if isinstance(data, list):
        return [from_dict(item) for item in data]
    
    if isinstance(data, tuple):
         return tuple(from_dict(item) for item in data)

    if not isinstance(data, dict):
        return data

    cls: type | None = None
    if "op" in data:
        cls = _OP_TO_CLASS.get(data["op"])
    elif "kind" in data:
        cls = _KIND_TO_CLASS.get(data["kind"])

    if cls and is_dataclass(cls):
        kwargs = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            
            # Special handling for enums, like RydbergSlot
            if f.type is RydbergSlot and isinstance(data[f.name], str):
                 kwargs[f.name] = RydbergSlot(data[f.name])
            else:
                 kwargs[f.name] = from_dict(data[f.name])
        
        return cls(**kwargs)

    # If it's a dict but not a recognized dataclass, reconstruct recursively
    return {key: from_dict(value) for key, value in data.items()}
