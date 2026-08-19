"""Test the architecture loader and builder."""

from pathlib import Path

import pytest

from minizac.architecture.loader import (
    ArchitectureSpec,
    build_architecture,
    load_from_json,
)


@pytest.fixture(scope="module")
def toy_arch_path() -> Path:
    """Get the path to the toy zoned architecture JSON file."""
    # Assuming tests are run from the project root
    return Path("hardware/toy_zoned.json")


@pytest.fixture(scope="module")
def toy_arch(toy_arch_path: Path) -> Architecture:
    """Load the toy zoned architecture."""
    return load_from_json(toy_arch_path)


def test_load_toy_zoned_architecture(toy_arch: Architecture):
    """Test loading the toy zoned architecture and check basic properties."""
    # --- Check counts ---
    assert len(toy_arch.storage_traps) == 4 * 8
    assert len(toy_arch.rydberg_sites) == 2 * 3
    assert len(toy_arch.aods) == 1

    # --- Check geometry of a few points ---
    # First storage trap (0, 0)
    trap0 = toy_arch.get_storage_trap(trap_id=0)
    assert trap0.row == 0
    assert trap0.col == 0
    assert trap0.position.x == pytest.approx(-10.5)
    assert trap0.position.y == pytest.approx(10.0)

    # First rydberg site (0, 0)
    site0 = toy_arch.get_rydberg_site(site_id=0)
    assert site0.row == 0
    assert site0.col == 0
    assert site0.center.x == pytest.approx(-10.0)
    assert site0.center.y == pytest.approx(-10.0)
    assert site0.left_position.x == pytest.approx(-11.0)
    assert site0.right_position.x == pytest.approx(-9.0)


def test_uniqueness_of_locations(toy_arch: Architecture):
    """Test that all physical locations in the architecture are unique."""
    storage_positions = {trap.position for trap in toy_arch.storage_traps}
    assert len(storage_positions) == len(toy_arch.storage_traps)

    rydberg_atom_positions = {
        pos
        for site in toy_arch.rydberg_sites
        for pos in (site.left_position, site.right_position)
    }
    assert len(rydberg_atom_positions) == len(toy_arch.rydberg_sites) * 2

    # Check that storage and rydberg zones don't overlap
    assert storage_positions.isdisjoint(rydberg_atom_positions)


def test_getters(toy_arch: Architecture):
    """Test the getter methods of the Architecture object."""
    trap0 = toy_arch.storage_traps[0]
    assert toy_arch.get_storage_trap(trap0.id) == trap0

    site1 = toy_arch.rydberg_sites[1]
    assert toy_arch.get_rydberg_site(site1.id) == site1

    with pytest.raises(KeyError):
        toy_arch.get_storage_trap(trap_id=-1)


@pytest.mark.parametrize(
    "invalid_params, error_msg",
    [
        ({"storage_rows": 0}, "Row, column, and AOD counts must be positive."),
        ({"storage_cols": -1}, "Row, column, and AOD counts must be positive."),
        ({"num_aods": 0}, "Row, column, and AOD counts must be positive."),
        ({"storage_spacing": -0.1}, "Spacing and separation must be non-negative."),
        ({"zone_separation": -1}, "Spacing and separation must be non-negative."),
    ],
)
def test_build_with_invalid_spec(invalid_params, error_msg):
    """Test that building an architecture with an invalid spec raises an error."""
    valid_params = {
        "storage_rows": 4,
        "storage_cols": 8,
        "rydberg_rows": 2,
        "rydberg_cols": 3,
        "storage_spacing": 3.0,
        "rydberg_site_spacing": 10.0,
        "pair_spacing": 2.0,
        "zone_separation": 20.0,
        "num_aods": 1,
    }
    spec = ArchitectureSpec(**{**valid_params, **invalid_params})
    with pytest.raises(ValueError, match=error_msg):
        build_architecture(spec)
