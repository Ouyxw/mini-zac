"""Unit tests for the state and transition data models."""

import pytest

from minizac.architecture import (
    AODId,
    QubitId,
    RydbergLocation,
    RydbergSiteId,
    RydbergSlot,
    StorageLocation,
    TrapId,
)
from minizac.ir import AtomMove, RearrangeJob
from minizac.state import PlacementState, apply_rearrange_job


def test_placement_collision():
    """Test that placing two qubits in the same location raises an error."""
    # Storage collision
    with pytest.raises(ValueError, match="Collision detected"):
        PlacementState(
            locations={
                QubitId(0): StorageLocation(TrapId(1)),
                QubitId(1): StorageLocation(TrapId(1)),
            }
        )

    # Rydberg slot collision
    loc = RydbergLocation(RydbergSiteId(2), RydbergSlot.LEFT)
    with pytest.raises(ValueError, match="Collision detected"):
        PlacementState(
            locations={
                QubitId(0): loc,
                QubitId(1): loc,
            }
        )


def test_legal_rydberg_pair():
    """Test that two qubits can occupy different slots in the same Rydberg site."""
    state = PlacementState(
        locations={
            QubitId(0): RydbergLocation(RydbergSiteId(2), RydbergSlot.LEFT),
            QubitId(1): RydbergLocation(RydbergSiteId(2), RydbergSlot.RIGHT),
        }
    )
    assert len(state.locations) == 2


def test_occupant_of():
    """Test the occupant_of method for reverse lookups."""
    loc0 = StorageLocation(TrapId(0))
    loc1 = RydbergLocation(RydbergSiteId(2), RydbergSlot.LEFT)
    state = PlacementState(
        locations={
            QubitId(5): loc0,
            QubitId(8): loc1,
        }
    )

    assert state.occupant_of(loc0) == QubitId(5)
    assert state.occupant_of(loc1) == QubitId(8)
    assert state.occupant_of(StorageLocation(TrapId(99))) is None


def test_apply_rearrange_job_valid():
    """Test a valid state transition with apply_rearrange_job."""
    loc_s0 = StorageLocation(TrapId(0))
    loc_s1 = StorageLocation(TrapId(1))
    loc_r0L = RydbergLocation(RydbergSiteId(0), RydbergSlot.LEFT)
    loc_r0R = RydbergLocation(RydbergSiteId(0), RydbergSlot.RIGHT)

    initial_state = PlacementState(
        locations={
            QubitId(0): loc_s0,
            QubitId(1): loc_s1,
        }
    )

    job = RearrangeJob(
        aod_id=AODId(0),
        moves=(
            AtomMove(QubitId(0), source=loc_s0, target=loc_r0L),
            AtomMove(QubitId(1), source=loc_s1, target=loc_r0R),
        ),
    )

    final_state = apply_rearrange_job(initial_state, job)

    expected_state = PlacementState(
        locations={
            QubitId(0): loc_r0L,
            QubitId(1): loc_r0R,
        }
    )
    assert final_state == expected_state


def test_apply_rearrange_job_invalid_source():
    """Test that a transition fails if the source location is incorrect."""
    loc_s0 = StorageLocation(TrapId(0))
    loc_s1 = StorageLocation(TrapId(1))
    loc_r0L = RydbergLocation(RydbergSiteId(0), RydbergSlot.LEFT)

    initial_state = PlacementState(
        locations={QubitId(0): loc_s0}
    )

    # Mismatched source
    job = RearrangeJob(
        aod_id=AODId(0),
        moves=(AtomMove(QubitId(0), source=loc_s1, target=loc_r0L),),
    )

    with pytest.raises(ValueError, match="Expected at"):
        apply_rearrange_job(initial_state, job)
