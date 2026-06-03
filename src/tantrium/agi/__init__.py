"""Aleph-Tekin AGI: certification-based intelligence grounded in 22 mathematical paradigms.

Not an LLM. Not a predictor. A certification machine.
Every claim requires a proof. Every gap is named precisely.
The manifold grows. Nothing is forgotten.
"""
from tantrium.agi.domains.bridge import SemanticBridge, PARADIGM_TO_THEOREMS, THEOREM_TO_PARADIGMS
from tantrium.agi.language.bootstrap import LanguageBootstrap, BootstrapResult
from tantrium.agi.core.codex import CODEX, CODEX_BY_ID, CodexObject, ParadigmResult
from tantrium.agi.core.encoder import UniversalEncoder, encode
from tantrium.agi.core.semantic import Concept, SemanticManifold
from tantrium.agi.core.network import AlephTekinNetwork, NetworkRun
from tantrium.agi.core.engine import AGIEngine
from tantrium.agi.reasoning.inference import InferenceChain, InferenceResult
from tantrium.agi.research.explorer import Explorer, ExplorationObjective, ExplorationResult
from tantrium.agi.language.speaker import Speaker, CertifiedStatement
from tantrium.agi.reasoning.thinker import Thinker, ThinkingResult, ThinkingLevel
from tantrium.agi.graph.tau_graph import TauGraph, TauNode, TauEdge
from tantrium.agi.graph.memory import SessionMemory, Turn
from tantrium.agi.graph.relations import (
    extract_relations,
    certify_and_add_edge,
    add_relations_from_text,
    propagate_subset,
    SEMANTIC_PARADIGMS,
)
from tantrium.agi.research.goal import Goal, GoalManifold, encode_goal
from tantrium.agi.research.actor import Actor, Action, ActionResult
from tantrium.agi.reasoning.generalization import HankelGeneralizer, DerivedConcept
from tantrium.agi.meta.topology import MomentTopology, MathRegion
from tantrium.agi.meta.paradigm import MetaParadigm, UniversalRule, ParadigmMoment, SelfCertResult
from tantrium.agi.domains.spectral import (
    SpectralMeasure,
    gram_spectrum,
    dna_measure,
    dna_window_measures,
    spectral_distance,
    spectral_window_diff,
    mutation_hotspots,
    moments_to_spectral,
)
from tantrium.agi.graph.anchors import (
    build_anchor_concepts,
    add_anchors_to_manifold,
    nearest_anchor,
    anchor_descriptions,
    is_anchor,
)
from tantrium.agi.research.autonomous import AutonomousObserver, Observation
from tantrium.agi.research.researcher import AutonomousResearcher, ResearchCycle, ResearchReport
from tantrium.agi.research.ingest import DataIngestor, IngestReport, IngestBatch
from tantrium.agi.reasoning.reasoner import TauReasoner, ReasoningResult, ChainStep
from tantrium.agi.reasoning.necessity import NecessityEngine, NecessityReport
from tantrium.agi.reasoning.planner import Planner, Plan, PlanStep
from tantrium.agi.language.generator import CertifiedGenerator, GenerationResult, GeneratedStep
from tantrium.agi.language.lang_topology import EnglishTopology, InjectionResult
from tantrium.agi.domains.molecular import (
    MolecularCertifier, CertificationReport, MoleculeReport,
    MoleculeGenerator, GenerationReport, GenerationCandidate,
)
from tantrium.agi.core.encoder import encode_smiles

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
    "DataIngestor",
    "IngestReport",
    "IngestBatch",
    "NecessityEngine",
    "NecessityReport",
    "TauReasoner",
    "ReasoningResult",
    "ChainStep",
    "Planner",
    "Plan",
    "PlanStep",
    "CertifiedGenerator",
    "GenerationResult",
    "GeneratedStep",
    "EnglishTopology",
    "InjectionResult",
    "MolecularCertifier",
    "CertificationReport",
    "MoleculeReport",
    "MoleculeGenerator",
    "GenerationReport",
    "GenerationCandidate",
    "encode_smiles",
]
