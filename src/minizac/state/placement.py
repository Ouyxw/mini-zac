"""Defines the physical placement state of all qubits."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ..architecture import QubitId
from .location import StaticLocation


@dataclass(frozen=True)
class PlacementState:
    """
    An immutable snapshot of the physical locations of all logical qubits.
    """

    locations: Mapping[QubitId, StaticLocation]

    def __post_init__(self) -> None:
        """Make the locations mapping immutable and check for collisions."""
        # Ensure the mapping is immutable
        object.__setattr__(self, "locations", MappingProxyType(dict(self.locations)))

        # Check for location collisions
        seen_locations: set[StaticLocation] = set()
        for location in self.locations.values():
            if location in seen_locations:
                raise ValueError(f"Collision detected: Multiple qubits assigned to {location}.")
            seen_locations.add(location)

    def occupant_of(self, location: StaticLocation) -> QubitId | None:
        """Find the qubit occupying a given location."""
        # This is an O(n) scan. If performance becomes an issue,
        # a reverse mapping can be added.
        for qubit, loc in self.locations.items():
            if loc == location:
                return qubit
        return None
