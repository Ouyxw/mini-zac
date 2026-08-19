from dataclasses import dataclass, field
from typing import Mapping

from .aod import AOD
from .ids import RydbergSiteId, TrapId
from .site import RydbergSite, StorageTrap


@dataclass(frozen=True, slots=True)
class Architecture:
    storage_traps: tuple[StorageTrap, ...]
    rydberg_sites: tuple[RydbergSite, ...]
    aods: tuple[AOD, ...]

    # Private attributes for quick lookups
    _storage_trap_map: Mapping[TrapId, StorageTrap] = field(
        init=False, repr=False, hash=False
    )
    _rydberg_site_map: Mapping[RydbergSiteId, RydbergSite] = field(
        init=False, repr=False, hash=False
    )

    def __post_init__(self) -> None:
        """Populate lookup maps after initialization."""
        object.__setattr__(
            self,
            "_storage_trap_map",
            {trap.id: trap for trap in self.storage_traps},
        )
        object.__setattr__(
            self,
            "_rydberg_site_map",
            {site.id: site for site in self.rydberg_sites},
        )

    def get_storage_trap(self, trap_id: TrapId) -> StorageTrap:
        """Get a storage trap by its ID."""
        return self._storage_trap_map[trap_id]

    def get_rydberg_site(self, site_id: RydbergSiteId) -> RydbergSite:
        """Get a Rydberg site by its ID."""
        return self._rydberg_site_map[site_id]
        
        

        
   

    
