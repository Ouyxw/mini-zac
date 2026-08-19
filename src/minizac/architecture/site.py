from dataclasses import dataclass
from enum import Enum

from .geometry import Position2D
from .ids import RydbergSiteId, TrapId


class RydbergSlot(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, slots=True)
class RydbergSite:
    id: RydbergSiteId
    row: int
    col: int
    left_position: Position2D
    right_position: Position2D

    @property
    def center(self) -> Position2D:
        return Position2D(
            x=(self.left_position.x + self.right_position.x) / 2,
            y=(self.left_position.y + self.right_position.y) / 2,
        )


@dataclass(frozen=True, slots=True)
class StorageTrap:
    id: TrapId
    row: int
    col: int
    position: Position2D