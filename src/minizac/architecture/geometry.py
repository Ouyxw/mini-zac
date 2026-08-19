import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position2D:
    x: float
    y: float

    def distance_to(self, other: "Position2D") -> float:
        return math.hypot(
            self.x - other.x,
            self.y - other.y,
        )
