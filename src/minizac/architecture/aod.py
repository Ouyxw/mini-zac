from dataclasses import dataclass

from .ids import AODId


@dataclass(frozen=True, slots=True)
class AOD:
    """Acousto-Optic Deflector."""

    id: AODId
