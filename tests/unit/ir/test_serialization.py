"""Unit tests for ZAIR serialization."""

import json

from minizac.architecture import (
    AODId,
    QubitId,
    RydbergLocation,
    RydbergSiteId,
    RydbergSlot,
    StorageLocation,
    TrapId,
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


def test_zair_roundtrip():
    """
    Test that a ZAIRProgram can be serialized to JSON and deserialized
    back to an identical object.
    """
    program = ZAIRProgram(
        instructions=(
            Initialize(
                placements=(
                    AtomPlacement(
                        QubitId(0),
                        StorageLocation(TrapId(0)),
                    ),
                    AtomPlacement(
                        QubitId(1),
                        StorageLocation(TrapId(1)),
                    ),
                ),
            ),
            RearrangeJob(
                aod_id=AODId(0),
                moves=(
                    AtomMove(
                        QubitId(0),
                        StorageLocation(TrapId(0)),
                        RydbergLocation(RydbergSiteId(0), RydbergSlot.LEFT),
                    ),
                    AtomMove(
                        QubitId(1),
                        StorageLocation(TrapId(1)),
                        RydbergLocation(RydbergSiteId(0), RydbergSlot.RIGHT),
                    ),
                ),
            ),
            RydbergStageOp(
                gates=(
                    RydbergCZ(
                        site_id=RydbergSiteId(0),
                        q0=QubitId(0),
                        q1=QubitId(1),
                    ),
                )
            ),
        ),
    )

    # Serialize to JSON string
    json_str = program.to_json(indent=4)

    # Deserialize back to a ZAIRProgram object
    reconstructed_program = ZAIRProgram.from_json(json_str)

    # The reconstructed object should be identical to the original
    assert reconstructed_program == program

    # Also, check the generated dict against the roadmap's example
    json_dict = json.loads(json_str)
    assert json_dict["version"] == "0.1"
    assert json_dict["instructions"][0]["op"] == "init"
    assert json_dict["instructions"][1]["op"] == "rearrange"
    assert json_dict["instructions"][1]["moves"][0]["target"]["kind"] == "rydberg"
    assert json_dict["instructions"][1]["moves"][0]["target"]["slot"] == "left"
