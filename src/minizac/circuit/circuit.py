"""Defines the logical circuit containing gates."""

from dataclasses import dataclass

from .gate import CZGate, Gate, UGate
from .qubit import QubitId


@dataclass(frozen=True, slots=True)
class Circuit:
    """A logical quantum circuit composed of a sequence of gates."""

    num_qubits: int
    gates: tuple[Gate, ...]

    def __post_init__(self) -> None:
        """Validate the circuit's integrity."""
        if self.num_qubits <= 0:
            raise ValueError("Circuit must contain at least one qubit.")

        for gate in self.gates:
            self._validate_gate(gate)

    def _validate_gate(self, gate: Gate) -> None:
        """Ensure all qubits in a gate are within the circuit's bounds."""
        qubits_to_check: list[QubitId] = []
        if isinstance(gate, UGate):
            qubits_to_check.append(gate.qubit)
        elif isinstance(gate, CZGate):
            qubits_to_check.extend([gate.q0, gate.q1])
        else:
            # This should be unreachable with the current Gate type definition
            raise TypeError(f"Unknown gate type: {type(gate)}")

        for qubit_id in qubits_to_check:
            if not (0 <= qubit_id < self.num_qubits):
                raise ValueError(
                    f"Qubit index {qubit_id} in {gate} is out of bounds "
                    f"for a circuit with {self.num_qubits} qubits."
                )
