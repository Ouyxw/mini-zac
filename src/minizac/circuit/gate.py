"""Defines the logical gates for the circuit IR."""

from dataclasses import dataclass

from .qubit import QubitId


@dataclass(frozen=True, slots=True)
class UGate:
    """Single-qubit universal rotation gate."""

    qubit: QubitId
    theta: float
    phi: float
    lam: float


@dataclass(frozen=True, slots=True)
class CZGate:
    """Controlled-Z gate between two qubits."""

    q0: QubitId
    q1: QubitId

    def __post_init__(self) -> None:
        """Validate that the two qubits are distinct."""
        if self.q0 == self.q1:
            raise ValueError("CZ gate requires two distinct qubits.")


Gate = UGate | CZGate
