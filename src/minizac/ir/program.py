"""Defines the top-level ZAIR program."""

import json
from dataclasses import dataclass
from typing import Any, Self

from . import serialization
from .instruction import Instruction


@dataclass(frozen=True, slots=True)
class ZAIRProgram:
    """A complete ZAIR program, consisting of a sequence of instructions."""

    instructions: tuple[Instruction, ...]
    version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        """Convert the program to a dictionary."""
        return serialization.to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a program from a dictionary."""
        obj = serialization.from_dict(data)
        if not isinstance(obj, cls):
            raise TypeError(f"Expected {cls.__name__}, but got {type(obj).__name__}")
        return obj

    def to_json(self, **kwargs: Any) -> str:
        """Convert the program to a JSON string."""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_json(cls, json_str: str, **kwargs: Any) -> Self:
        """Create a program from a JSON string."""
        data = json.loads(json_str, **kwargs)
        return cls.from_dict(data)
