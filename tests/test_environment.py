from qiskit import QuantumCircuit, transpile


def test_qiskit_frontend() -> None:
    circuit = QuantumCircuit(2)

    circuit.h(0)
    circuit.cx(0, 1)

    lowered = transpile(circuit, basis_gates=["u3", "cx"], optimization_level=0)

    operation_names = {instruction.operation.name for instruction in lowered.data}

    assert operation_names <= {"u3", "cx"}
