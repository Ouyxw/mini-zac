"""Defines a stage in the circuit execution, typically for parallel two-qubit gates."""

from dataclasses import dataclass

from .gate import CZGate
from .qubit import QubitId


@dataclass(frozen=True, slots=True)
class RydbergStage:
    """A collection of two-qubit gates that can be executed in parallel."""

    index: int
    gates: tuple[CZGate, ...]

    def __post_init__(self) -> None:
        """Validate that no qubit participates in more than one gate per stage."""
        seen_qubits: set[QubitId] = set()
        for gate in self.gates:
            if gate.q0 in seen_qubits or gate.q1 in seen_qubits:
                raise ValueError(
                    f"Qubit involved in more than one gate in stage {self.index}."
                )
            seen_qubits.add(gate.q0)
            seen_qubits.add(gate.q1)
