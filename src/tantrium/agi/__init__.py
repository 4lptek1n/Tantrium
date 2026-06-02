"""Aleph-Tekin AGI: certification-based intelligence grounded in 22 mathematical paradigms.

Not an LLM. Not a predictor. A certification machine.
Every claim requires a proof. Every gap is named precisely.
The manifold grows. Nothing is forgotten.
"""
from tantrium.agi.bridge import SemanticBridge, PARADIGM_TO_THEOREMS, THEOREM_TO_PARADIGMS
from tantrium.agi.language import LanguageBootstrap, BootstrapResult
from tantrium.agi.codex import CODEX, CODEX_BY_ID, CodexObject, ParadigmResult
from tantrium.agi.encoder import UniversalEncoder, encode
from tantrium.agi.semantic import Concept, SemanticManifold
from tantrium.agi.network import AlephTekinNetwork, NetworkRun
from tantrium.agi.engine import AGIEngine
from tantrium.agi.inference import InferenceChain, InferenceResult
from tantrium.agi.explorer import Explorer, ExplorationObjective, ExplorationResult
from tantrium.agi.speaker import Speaker, CertifiedStatement
from tantrium.agi.thinker import Thinker, ThinkingResult, ThinkingLevel
from tantrium.agi.tau_graph import TauGraph, TauNode, TauEdge
from tantrium.agi.memory import SessionMemory, Turn
from tantrium.agi.relations import (
    extract_relations,
    certify_and_add_edge,
    add_relations_from_text,
    propagate_subset,
    SEMANTIC_PARADIGMS,
)
from tantrium.agi.goal import Goal, GoalManifold, encode_goal
from tantrium.agi.actor import Actor, Action, ActionResult
from tantrium.agi.generalization import HankelGeneralizer, DerivedConcept
from tantrium.agi.topology import MomentTopology, MathRegion
from tantrium.agi.meta import MetaParadigm, UniversalRule, ParadigmMoment, SelfCertResult
from tantrium.agi.spectral import (
    SpectralMeasure,
    gram_spectrum,
    dna_measure,
    dna_window_measures,
    spectral_distance,
    spectral_window_diff,
    mutation_hotspots,
    moments_to_spectral,
)
from tantrium.agi.anchors import (
    build_anchor_concepts,
    add_anchors_to_manifold,
    nearest_anchor,
    anchor_descriptions,
    is_anchor,
)
from tantrium.agi.autonomous import AutonomousObserver, Observation
from tantrium.agi.researcher import AutonomousResearcher, ResearchCycle, ResearchReport

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
    "LanguageBootstrap",
    "BootstrapResult",
    "Thinker",
    "ThinkingResult",
    "ThinkingLevel",
    "TauGraph",
    "TauNode",
    "TauEdge",
    "SessionMemory",
    "Turn",
    "extract_relations",
    "certify_and_add_edge",
    "add_relations_from_text",
    "propagate_subset",
    "SEMANTIC_PARADIGMS",
    "Goal",
    "GoalManifold",
    "encode_goal",
    "Actor",
    "Action",
    "ActionResult",
    "HankelGeneralizer",
    "DerivedConcept",
    "MomentTopology",
    "MathRegion",
    "MetaParadigm",
    "UniversalRule",
    "ParadigmMoment",
    "SelfCertResult",
    "SpectralMeasure",
    "gram_spectrum",
    "dna_measure",
    "dna_window_measures",
    "spectral_distance",
    "spectral_window_diff",
    "mutation_hotspots",
    "moments_to_spectral",
    "build_anchor_concepts",
    "add_anchors_to_manifold",
    "nearest_anchor",
    "anchor_descriptions",
    "is_anchor",
    "AutonomousObserver",
    "Observation",
    "AutonomousResearcher",
    "ResearchCycle",
    "ResearchReport",
]
