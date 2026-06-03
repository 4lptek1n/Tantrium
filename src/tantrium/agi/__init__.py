"""Backward-compatible re-exports: tantrium.agi.* → tantrium.*

All new code should import from tantrium.core, tantrium.graph, etc.
This shim keeps legacy imports working.
"""
# Core
from tantrium.core.codex import PARADIGMS, PARADIGM_BY_ID, CertifiableObject, ParadigmResult
from tantrium.core.encoder import UniversalEncoder, encode, encode_smiles
from tantrium.core.semantic import Concept, SemanticManifold
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.engine import CertificationEngine

# Graph
from tantrium.graph.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeEdge
from tantrium.graph.memory import SessionMemory, Turn
from tantrium.graph.relations import (
    extract_relations, certify_and_add_edge, add_relations_from_text,
    propagate_subset, SEMANTIC_PARADIGMS,
)
from tantrium.graph.anchors import (
    build_anchor_concepts, add_anchors_to_manifold, nearest_anchor,
    anchor_descriptions, is_anchor,
)

# Reasoning
from tantrium.reasoning.reasoner import GraphReasoner, ReasoningResult, ChainStep
from tantrium.reasoning.inference import InferenceChain, InferenceResult
from tantrium.reasoning.necessity import NecessityEngine, NecessityReport
from tantrium.reasoning.generalization import HankelGeneralizer, DerivedConcept
from tantrium.reasoning.thinker import Thinker, ThinkingResult, ThinkingLevel
from tantrium.reasoning.planner import Planner, Plan, PlanStep

# Research
from tantrium.research.explorer import Explorer, ExplorationObjective, ExplorationResult
from tantrium.research.autonomous import AutonomousObserver, Observation
from tantrium.research.researcher import AutonomousResearcher, ResearchCycle, ResearchReport
from tantrium.research.ingest import DataIngestor, IngestReport, IngestBatch
from tantrium.research.proof_loop import ProofLoop, LoopReport, LoopCycle
from tantrium.research.goal import Goal, GoalManifold, encode_goal
from tantrium.research.actor import Actor, Action, ActionResult

# Language
from tantrium.language.speaker import Speaker, CertifiedStatement
from tantrium.language.generator import CertifiedGenerator, GenerationResult, GeneratedStep
from tantrium.language.bootstrap import LanguageBootstrap, BootstrapResult
from tantrium.language.lang_topology import EnglishTopology, InjectionResult

# Domains
from tantrium.domains.bridge import SemanticBridge, PARADIGM_TO_THEOREMS, THEOREM_TO_PARADIGMS
from tantrium.domains.certifier import MolecularCertifier, CertificationReport, MoleculeReport
from tantrium.domains.generator import MoleculeGenerator, GenerationReport, GenerationCandidate
from tantrium.domains.spectral import (
    SpectralMeasure, gram_spectrum, dna_measure, dna_window_measures,
    spectral_distance, spectral_window_diff, mutation_hotspots, moments_to_spectral,
)

# Meta
from tantrium.meta.paradigm import MetaParadigm, UniversalRule, ParadigmMoment, SelfCertResult
from tantrium.meta.topology import MomentTopology, MathRegion

# Backward-compatible aliases
CODEX = PARADIGMS
CODEX_BY_ID = PARADIGM_BY_ID
CodexObject = CertifiableObject
AlephTekinNetwork = CertificationPipeline
NetworkRun = CertificationRun
AGIEngine = CertificationEngine
TauGraph = KnowledgeGraph
TauNode = KnowledgeNode
TauEdge = KnowledgeEdge
TauReasoner = GraphReasoner

__all__ = [
    "SemanticBridge",
    "PARADIGM_TO_THEOREMS",
    "THEOREM_TO_PARADIGMS",
    # New names
    "PARADIGMS",
    "PARADIGM_BY_ID",
    "CertifiableObject",
    "CertificationPipeline",
    "CertificationRun",
    "CertificationEngine",
    "KnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeEdge",
    "GraphReasoner",
    # Backward-compatible aliases
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
    "ProofLoop",
    "LoopReport",
    "LoopCycle",
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
