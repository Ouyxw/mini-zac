"""Defines physical locations for qubits in the hardware architecture."""

from dataclasses import dataclass

from ..architecture import RydbergSiteId, RydbergSlot, TrapId


@dataclass(frozen=True, slots=True)
class StorageLocation:
    """A qubit located in a storage zone trap."""

    trap_id: TrapId


@dataclass(frozen=True, slots=True)
class RydbergLocation:
    """A qubit located in an entanglement zone slot."""

    site_id: RydbergSiteId
    slot: RydbergSlot


StaticLocation = StorageLocation | RydbergLocation
