"""
M0 Integration Test: Bell State Preparation Flow
"""
from pathlib import Path

import pytest

from minizac.architecture import (
    AODId,
    Architecture,
    QubitId,
    RydbergLocation,
    RydbergSiteId,
    RydbergSlot,
    StorageLocation,
    TrapId,
    load_from_json,
)
from minizac.ir import (
    AtomMove,
    AtomPlacement,
    Initialize,
    RearrangeJob,
    RydbergCZ,
    RydbergStageOp,
    ZAIRProgram,
)
from minizac.state import PlacementState, apply_rearrange_job


@pytest.fixture(scope="module")
def toy_arch() -> Architecture:
    """Load the toy zoned architecture."""
    path = Path("hardware/toy_zoned.json")
    return load_from_json(path)


def test_bell_state_flow(toy_arch: Architecture):
    """
    Tests the flow of creating a Bell state by integrating architecture,
    state, and IR components.
    """
    # 1. Define logical qubits and their physical locations
    q0, q1 = QubitId(0), QubitId(1)
    
    # Initial locations in storage
    s0 = StorageLocation(TrapId(0))
    s1 = StorageLocation(TrapId(1))

    # Target locations in a Rydberg site
    r_site_id = RydbergSiteId(0)
    r0_left = RydbergLocation(r_site_id, RydbergSlot.LEFT)
    r0_right = RydbergLocation(r_site_id, RydbergSlot.RIGHT)

    # 2. Define the ZAIRProgram, starting with initialization
    # This represents the intended sequence of hardware operations.
    program = ZAIRProgram(
        instructions=(
            Initialize(
                placements=(
                    AtomPlacement(q0, s0),
                    AtomPlacement(q1, s1),
                ),
            ),
            RearrangeJob(
                aod_id=AODId(0),
                moves=(
                    AtomMove(q0, source=s0, target=r0_left),
                    AtomMove(q1, source=s1, target=r0_right),
                ),
            ),
            RydbergStageOp(
                gates=(RydbergCZ(site_id=r_site_id, q0=q0, q1=q1),)
            ),
        ),
    )
    
    # 3. Simulate the state transitions based on the program
    
    # Get the initialization instruction and create the initial state
    init_op = program.instructions[0]
    assert isinstance(init_op, Initialize)
    initial_state = PlacementState(
        locations={p.qubit: p.location for p in init_op.placements}
    )
    
    # Verify initial state
    assert initial_state.occupant_of(s0) == q0
    assert initial_state.occupant_of(s1) == q1
    
    # Get the rearrangement job
    rearrange_op = program.instructions[1]
    assert isinstance(rearrange_op, RearrangeJob)

    # Apply the job to get the new state
    final_state = apply_rearrange_job(initial_state, rearrange_op)

    # 4. Verify the final state after rearrangement
    assert final_state.occupant_of(r0_left) == q0
    assert final_state.occupant_of(r0_right) == q1
    assert final_state.occupant_of(s0) is None
    assert final_state.occupant_of(s1) is None
    
    # This completes the M0 integration test. We have successfully modeled
    # the state transition required for a two-qubit gate, verifying that
    # the architecture, state, and IR models work together.
