"""Aleph-Tekin AGI: certification-based intelligence grounded in 22 mathematical paradigms.

Not an LLM. Not a predictor. A certification machine.
Every claim requires a proof. Every gap is named precisely.
The manifold grows. Nothing is forgotten.
"""
from tantrium.agi.bridge import SemanticBridge, PARADIGM_TO_THEOREMS, THEOREM_TO_PARADIGMS
from tantrium.agi.codex import CODEX, CODEX_BY_ID, CodexObject, ParadigmResult
from tantrium.agi.encoder import UniversalEncoder, encode
from tantrium.agi.semantic import Concept, SemanticManifold
from tantrium.agi.network import AlephTekinNetwork, NetworkRun
from tantrium.agi.engine import AGIEngine
from tantrium.agi.inference import InferenceChain, InferenceResult
from tantrium.agi.explorer import Explorer, ExplorationObjective, ExplorationResult
from tantrium.agi.speaker import Speaker, CertifiedStatement

__all__ = [
    "SemanticBridge",
    "PARADIGM_TO_THEOREMS",
    "THEOREM_TO_PARADIGMS",
    "CODEX",
    "CODEX_BY_ID",
    "CodexObject",
    "ParadigmResult",
    "UniversalEncoder",
    "encode",
    "Concept",
    "SemanticManifold",
    "AlephTekinNetwork",
    "NetworkRun",
    "AGIEngine",
    "InferenceChain",
    "InferenceResult",
    "Explorer",
    "ExplorationObjective",
    "ExplorationResult",
    "Speaker",
    "CertifiedStatement",
]
