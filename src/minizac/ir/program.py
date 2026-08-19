"""Defines the top-level ZAIR program."""

from dataclasses import dataclass

from .instruction import Instruction


@dataclass(frozen=True, slots=True)
class ZAIRProgram:
    """A complete ZAIR program, consisting of a sequence of instructions."""

    instructions: tuple[Instruction, ...]
