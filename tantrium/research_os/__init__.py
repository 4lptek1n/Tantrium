"""Tantrium autonomous mathematical research OS.

This package is a deterministic research orchestration layer above the sealed
Tantrium proof and autosolver artifacts. It records evidence, candidates,
proof attempts, counterexample searches, formalization work queues, and
campaign reports without inflating mathematical closure statuses.
"""

from .proof_state import FINAL_MATH_STATUSES, RESEARCH_STATUSES
from .scheduler import CAMPAIGNS, expand_campaigns

__all__ = ["CAMPAIGNS", "FINAL_MATH_STATUSES", "RESEARCH_STATUSES", "expand_campaigns"]
