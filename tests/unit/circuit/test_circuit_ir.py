"""Unit tests for the Circuit IR data models."""

import pytest

from minizac.circuit import CZGate, Circuit, QubitId, RydbergStage, UGate


def test_cz_self_interaction():
    """Test that a CZ gate requires two distinct qubits."""
    with pytest.raises(ValueError, match="CZ gate requires two distinct qubits"):
        CZGate(QubitId(0), QubitId(0))


def test_circuit_qubit_bounds():
    """Test that gates in a circuit must use qubits within bounds."""
    # UGate out of bounds
    with pytest.raises(ValueError, match="is out of bounds"):
        Circuit(num_qubits=2, gates=(UGate(QubitId(2), 0, 0, 0),))

    # CZGate out of bounds
    with pytest.raises(ValueError, match="is out of bounds"):
        Circuit(num_qubits=2, gates=(CZGate(QubitId(1), QubitId(2)),))

    # Valid circuit
    circuit = Circuit(
        num_qubits=3,
        gates=(
            UGate(QubitId(0), 1, 1, 1),
            CZGate(QubitId(1), QubitId(2)),
        ),
    )
    assert circuit.num_qubits == 3


def test_circuit_invalid_num_qubits():
    """Test that a circuit must have a positive number of qubits."""
    with pytest.raises(ValueError, match="must contain at least one qubit"):
        Circuit(num_qubits=0, gates=())


def test_rydberg_stage_conflict():
    """Test that a qubit cannot be used in two gates in the same stage."""
    gate1 = CZGate(QubitId(0), QubitId(1))
    gate2 = CZGate(QubitId(2), QubitId(0))  # Qubit 0 is reused

    with pytest.raises(ValueError, match="involved in more than one gate"):
        RydbergStage(index=0, gates=(gate1, gate2))

    # Valid stage
    gate3 = CZGate(QubitId(2), QubitId(3))
    stage = RydbergStage(index=0, gates=(gate1, gate3))
    assert len(stage.gates) == 2
