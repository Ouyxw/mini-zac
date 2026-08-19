"""Load an architecture from a JSON definition."""

import json
from dataclasses import dataclass
from pathlib import Path

from .aod import AOD
from .architecture import Architecture
from .geometry import Position2D
from .ids import AODId, RydbergSiteId, TrapId
from .site import RydbergSite, StorageTrap


@dataclass(frozen=True)
class ArchitectureSpec:
    """Configuration specification for a zoned architecture."""
    storage_rows: int
    storage_cols: int
    rydberg_rows: int
    rydberg_cols: int
    storage_spacing: float
    rydberg_site_spacing: float
    pair_spacing: float
    zone_separation: float
    num_aods: int


def build_architecture(spec: ArchitectureSpec) -> Architecture:
    """Build an Architecture object from a specification."""
    # --- Validation ---
    if not (spec.storage_rows > 0 and spec.storage_cols > 0 and
            spec.rydberg_rows > 0 and spec.rydberg_cols > 0 and
            spec.num_aods > 0):
        raise ValueError("Row, column, and AOD counts must be positive.")

    if not (spec.storage_spacing >= 0 and spec.rydberg_site_spacing >= 0 and
            spec.pair_spacing >= 0 and spec.zone_separation >= 0):
        raise ValueError("Spacing and separation must be non-negative.")

    # --- Storage Zone ---
    storage_traps = []
    trap_id_counter = 0
    s_width = (spec.storage_cols - 1) * spec.storage_spacing
    for r in range(spec.storage_rows):
        for c in range(spec.storage_cols):
            pos = Position2D(
                x=(-s_width / 2) + c * spec.storage_spacing,
                y=(spec.zone_separation / 2) + r * spec.storage_spacing,
            )
            storage_traps.append(
                StorageTrap(id=TrapId(trap_id_counter), row=r, col=c, position=pos)
            )
            trap_id_counter += 1

    # --- Entanglement Zone ---
    rydberg_sites = []
    site_id_counter = 0
    e_width = (spec.rydberg_cols - 1) * spec.rydberg_site_spacing
    for r in range(spec.rydberg_rows):
        for c in range(spec.rydberg_cols):
            center_x = (-e_width / 2) + c * spec.rydberg_site_spacing
            center_y = (-spec.zone_separation / 2) - r * spec.rydberg_site_spacing
            left_pos = Position2D(x=center_x - spec.pair_spacing / 2, y=center_y)
            right_pos = Position2D(x=center_x + spec.pair_spacing / 2, y=center_y)
            rydberg_sites.append(
                RydbergSite(
                    id=RydbergSiteId(site_id_counter),
                    row=r,
                    col=c,
                    left_position=left_pos,
                    right_position=right_pos,
                )
            )
            site_id_counter += 1

    # --- AODs ---
    aods = [AOD(id=AODId(i)) for i in range(spec.num_aods)]

    return Architecture(
        storage_traps=tuple(storage_traps),
        rydberg_sites=tuple(rydberg_sites),
        aods=tuple(aods),
    )


def load_from_json(path: Path) -> Architecture:
    """Load an architecture from a JSON file."""
    config = json.loads(path.read_text())
    
    spec = ArchitectureSpec(
        storage_rows=config["storage"]["rows"],
        storage_cols=config["storage"]["cols"],
        storage_spacing=config["storage"]["spacing"],
        rydberg_rows=config["entanglement"]["rows"],
        rydberg_cols=config["entanglement"]["cols"],
        rydberg_site_spacing=config["entanglement"]["site_spacing"],
        pair_spacing=config["entanglement"]["pair_spacing"],
        zone_separation=config["zone_separation"],
        num_aods=config["aod"]["count"],
    )
    
    return build_architecture(spec)
