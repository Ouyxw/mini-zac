"""Test the architecture loader."""

from pathlib import Path

import pytest

from minizac.architecture.loader import load_from_json


@pytest.fixture(scope="module")
def toy_arch_path() -> Path:
    """Get the path to the toy zoned architecture JSON file."""
    # Assuming tests are run from the project root
    return Path("hardware/toy_zoned.json")


def test_load_toy_zoned_architecture(toy_arch_path: Path):
    """Test loading the toy zoned architecture."""
    arch = load_from_json(toy_arch_path)

    # --- Check counts ---
    assert len(arch.storage_traps) == 4 * 8
    assert len(arch.rydberg_sites) == 2 * 3
    assert len(arch.aods) == 1

    # --- Check geometry of a few points ---
    # First storage trap (0, 0)
    trap0 = arch.get_storage_trap(trap_id=0)
    assert trap0.row == 0
    assert trap0.col == 0
    # Expected position: x = -10.5, y = 10.0
    assert trap0.position.x == pytest.approx(-10.5)
    assert trap0.position.y == pytest.approx(10.0)

    # First rydberg site (0, 0)
    site0 = arch.get_rydberg_site(site_id=0)
    assert site0.row == 0
    assert site0.col == 0
    # Expected center: x = -10.0, y = -10.0
    # Expected pair positions: x = -11.0, -9.0
    assert site0.center.x == pytest.approx(-10.0)
    assert site0.center.y == pytest.approx(-10.0)
    assert site0.left_position.x == pytest.approx(-11.0)
    assert site0.right_position.x == pytest.approx(-9.0)

    # --- Check uniqueness of locations ---
    storage_positions = {trap.position for trap in arch.storage_traps}
    assert len(storage_positions) == len(arch.storage_traps)

    rydberg_atom_positions = set()
    for site in arch.rydberg_sites:
        rydberg_atom_positions.add(site.left_position)
        rydberg_atom_positions.add(site.right_position)
    assert len(rydberg_atom_positions) == len(arch.rydberg_sites) * 2

    # Check that storage and rydberg zones don't overlap
    assert storage_positions.isdisjoint(rydberg_atom_positions)
