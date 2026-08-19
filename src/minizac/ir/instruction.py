"""Defines the ZAIR-like execution instructions for the hardware."""

from dataclasses import dataclass

from ..architecture import AODId, QubitId, RydbergSiteId
from ..state import StaticLocation


@dataclass(frozen=True, slots=True)
class AtomPlacement:
    """Specifies the initial placement of a single qubit."""
    qubit: QubitId
    location: StaticLocation


@dataclass(frozen=True, slots=True)
class Initialize:
    """Instruction to prepare the initial arrangement of atoms."""
    op = "init"
    placements: tuple[AtomPlacement, ...]


@dataclass(frozen=True, slots=True)
class OneQOp:
    """Instruction for a single-qubit gate operation."""
    op = "1q_op"
    qubit: QubitId
    theta: float
    phi: float
    lam: float


@dataclass(frozen=True, slots=True)
class AtomMove:
    """Specifies the movement of a single atom from a source to a target."""
    qubit: QubitId
    source: StaticLocation
    target: StaticLocation


@dataclass(frozen=True, slots=True)
class RearrangeJob:
    """Instruction for a batch of atom movements using a single AOD."""
    op = "rearrange"
    aod_id: AODId
    moves: tuple[AtomMove, ...]


@dataclass(frozen=True, slots=True)
class RydbergCZ:
    """Specifies a CZ gate executed at a specific Rydberg site."""
    site_id: RydbergSiteId
    q0: QubitId
    q1: QubitId


@dataclass(frozen=True, slots=True)
class RydbergStageOp:
    """Instruction for a set of parallel CZ gates."""
    op = "rydberg_stage"
    gates: tuple[RydbergCZ, ...]


Instruction = Initialize | OneQOp | RearrangeJob | RydbergStageOp
