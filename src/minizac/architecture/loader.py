"""Load an architecture from a JSON definition."""

import json
from pathlib import Path

from .aod import AOD
from .architecture import Architecture, StorageTrap
from .geometry import Position2D
from .ids import AODId, RydbergSiteId, TrapId
from .site import RydbergSite


def load_from_json(path: Path) -> Architecture:
    """Load an architecture from a JSON file."""
    config = json.loads(path.read_text())

    # --- Storage Zone ---
    s_config = config["storage"]
    s_rows = s_config["rows"]
    s_cols = s_config["cols"]
    s_spacing = s_config["spacing"]
    zone_sep = config["zone_separation"]

    storage_traps = []
    trap_id_counter = 0
    # Center the grid horizontally
    s_width = (s_cols - 1) * s_spacing
    for r in range(s_rows):
        for c in range(s_cols):
            pos = Position2D(
                x=(-s_width / 2) + c * s_spacing,
                y=(zone_sep / 2) + r * s_spacing,
            )
            storage_traps.append(
                StorageTrap(id=TrapId(trap_id_counter), row=r, col=c, position=pos)
            )
            trap_id_counter += 1

    # --- Entanglement Zone ---
    e_config = config["entanglement"]
    e_rows = e_config["rows"]
    e_cols = e_config["cols"]
    site_spacing = e_config["site_spacing"]
    pair_spacing = e_config["pair_spacing"]

    rydberg_sites = []
    site_id_counter = 0
    # Center the grid horizontally
    e_width = (e_cols - 1) * site_spacing
    for r in range(e_rows):
        for c in range(e_cols):
            center_x = (-e_width / 2) + c * site_spacing
            center_y = (-zone_sep / 2) - r * site_spacing

            left_pos = Position2D(x=center_x - pair_spacing / 2, y=center_y)
            right_pos = Position2D(x=center_x + pair_spacing / 2, y=center_y)

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
    aods = [AOD(id=AODId(i)) for i in range(config["aod"]["count"])]

    return Architecture(
        storage_traps=tuple(storage_traps),
        rydberg_sites=tuple(rydberg_sites),
        aods=tuple(aods),
    )