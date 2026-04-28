"""Core system interfaces for Tantrium.

A Tantrium system is any mathematical or scientific object family that can
be generated, analyzed, and verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Protocol


class Generator(Protocol):
    """Protocol for object generators."""

    def __call__(self, **kwargs: Any) -> Any:
        """Generate an object from keyword parameters."""


@dataclass
class DiscoveryResult:
    """Structured output from a Tantrium discovery run."""

    name: str
    status: str
    claims: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    open_questions: List[str] = field(default_factory=list)


@dataclass
class System:
    """A symbolic-computational discovery target."""

    name: str
    description: str
    generator: Callable[..., Any] | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def generate(self, **kwargs: Any) -> Any:
        """Generate an object from this system."""
        if self.generator is None:
            raise NotImplementedError("No generator has been attached to this system.")
        return self.generator(**kwargs)
