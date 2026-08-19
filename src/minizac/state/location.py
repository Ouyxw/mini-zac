"""Defines physical locations for qubits in the hardware architecture."""

from dataclasses import dataclass, field
from typing import Literal

from ..architecture import RydbergSiteId, RydbergSlot, TrapId


@dataclass(frozen=True, slots=True)
class StorageLocation:
    """A qubit located in a storage zone trap."""

    trap_id: TrapId
    kind: Literal["storage"] = field(default="storage", init=False)


@dataclass(frozen=True, slots=True)
class RydbergLocation:
    """A qubit located in an entanglement zone slot."""

    site_id: RydbergSiteId
    slot: RydbergSlot
    kind: Literal["rydberg"] = field(default="rydberg", init=False)


StaticLocation = StorageLocation | RydbergLocation
