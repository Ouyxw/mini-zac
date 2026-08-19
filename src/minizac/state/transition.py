"""Functions for transitioning between placement states."""

from ..ir import RearrangeJob
from .placement import PlacementState


def apply_rearrange_job(
    state: PlacementState,
    job: RearrangeJob,
) -> PlacementState:
    """
    Applies a rearrangement job to a placement state to produce a new state.

    This function does not validate the legality of the moves themselves (e.g.,
    AOD trajectory constraints), but it does validate the start and end states.

    Args:
        state: The initial placement state.
        job: The rearrangement job to apply.

    Returns:
        A new PlacementState reflecting the locations after the moves.

    Raises:
        ValueError: If a move is invalid (e.g., source location mismatch).
    """
    new_locations = dict(state.locations)

    for move in job.moves:
        # Verify that the qubit is at the expected source location
        current_loc = new_locations.get(move.qubit)
        if current_loc != move.source:
            raise ValueError(
                f"Cannot move qubit {move.qubit}: Expected at {move.source}, "
                f"but was at {current_loc}."
            )

        # Update the qubit's location to the target
        new_locations[move.qubit] = move.target

    return PlacementState(locations=new_locations)
