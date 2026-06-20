"""Tantrium: structure-first symbolic discovery framework."""

from tantrium.ai import (
    AI,
    AskResult,
    DesignResult,
    DiscoverResult,
    GenResult,
    MolResult,
    ReasonResult,
)
from tantrium.core.collision import CollisionHunter, CollisionReport
from tantrium.core.confidence import Confidence, calibrate
from tantrium.core.encoder import UniversalEncoder, encode, encode_smiles
from tantrium.core.engine import CertificationEngine
from tantrium.core.inverse import DesignCandidate, DesignReport, InverseTransport
from tantrium.core.metric import canonical_distance, l1_distance
from tantrium.core.metric import distance as metric_distance
from tantrium.core.molecular_genesis import (
    GenesisCandidate,
    MolecularGenesis,
)
from tantrium.core.molecular_genesis import (
    GenesisReport as MolGenesisReport,
)
from tantrium.core.molecular_space import ArrangementResult, MolecularSpace, MolPoint, MorphResult
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.quantum_moments import (
    FreeCumulants,
    QuantumSignature,
    bounded_kappa_distance,
    free_entropy,
)
from tantrium.core.reconstruct import (
    ReconstructedMeasure,
    reconstruct_measure,
    reconstruction_fidelity,
)
from tantrium.core.semantic import AdmissionResult, Concept, SemanticManifold
from tantrium.core.transport import CertifiedTransport, TransportCertificate, TransportRanking
from tantrium.core.truth import TruthCertificate, TruthCertifier
from tantrium.core.unified import CoreMachine, UnifiedCertificate
from tantrium.domains.spectral import (
    SpectralMeasure,
    dna_measure,
    gram_spectrum,
    moments_to_spectral,
    spectral_distance,
)
from tantrium.graph.knowledge_graph import KnowledgeEdge, KnowledgeGraph, KnowledgeNode
from tantrium.graph.memory import SessionMemory, Turn
from tantrium.meta.paradigm import MetaParadigm, ParadigmMoment, SelfCertResult, UniversalRule
from tantrium.meta.self_model import SelfModel, SelfReflection
from tantrium.meta.synthesis import (
    BridgeResult,
    ConceptSynthesizer,
    EnergyProfile,
    GenesisEntry,
    GenesisReport,
    ResonanceResult,
)
from tantrium.meta.topology import MathRegion, MomentTopology
from tantrium.meta.vision import CosmicFrame, CosmicVision
from tantrium.perception import (
    encode_image,
    encode_matrix,
    encode_signal,
    signal_autocorrelation,
)
from tantrium.proof.certificate import Cell, Certificate, TransportEdge
from tantrium.proof.dyadic_flow import FlowPolicy, solve_greedy
from tantrium.reasoning.gap_finder import Gap, GapFinder
from tantrium.reasoning.generalization import DerivedConcept, HankelGeneralizer
from tantrium.reasoning.necessity import ManifoldGap, NecessaryEdge, NecessityReport
from tantrium.reasoning.planner import Plan, Planner, PlanStep
from tantrium.reasoning.reasoner import ChainStep, GraphReasoner, ReasoningResult
from tantrium.reasoning.thinker import ThinkingLevel, ThinkingResult
from tantrium.reasoning.wonder import WonderScore, WonderScorer
from tantrium.research.actor import Action, ActionResult
from tantrium.research.explorer import ExplorationObjective, ExplorationResult
from tantrium.research.goal import Goal, GoalManifold
from tantrium.research.proof_loop import LoopCycle, LoopReport, ProofLoop

__all__ = [
    # Core SDK
    "AI",
    "AskResult",
    "MolResult",
    "GenResult",
    "ReasonResult",
    "DiscoverResult",
    "DesignResult",
    "InverseTransport",
    "DesignCandidate",
    "DesignReport",
    "MolecularSpace",
    "MolPoint",
    "ArrangementResult",
    "MorphResult",
    "CertificationEngine",
    "CertificationPipeline",
    "CertificationRun",
    "UniversalEncoder",
    "encode",
    "encode_smiles",
    "Concept",
    "SemanticManifold",
    "AdmissionResult",
    "CertifiedTransport",
    "TransportCertificate",
    "TransportRanking",
    # Proof primitives
    "Cell",
    "Certificate",
    "TransportEdge",
    "solve_greedy",
    "FlowPolicy",
    # Graph
    "KnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeEdge",
    "SessionMemory",
    "Turn",
    # Research
    "ProofLoop",
    "LoopReport",
    "LoopCycle",
    "ExplorationObjective",
    "ExplorationResult",
    "Goal",
    "GoalManifold",
    "Action",
    "ActionResult",
    # Reasoning
    "ThinkingResult",
    "ThinkingLevel",
    "NecessityReport",
    "NecessaryEdge",
    "ManifoldGap",
    "Gap",
    "GapFinder",
    "WonderScore",
    "WonderScorer",
    "DerivedConcept",
    "HankelGeneralizer",
    "ChainStep",
    "ReasoningResult",
    "GraphReasoner",
    "Plan",
    "PlanStep",
    "Planner",
    # Spectral
    "SpectralMeasure",
    "gram_spectrum",
    "spectral_distance",
    "dna_measure",
    "moments_to_spectral",
    # Meta
    "MetaParadigm",
    "UniversalRule",
    "ParadigmMoment",
    "SelfCertResult",
    "MomentTopology",
    "MathRegion",
    "CosmicVision",
    "CosmicFrame",
    "SelfModel",
    "SelfReflection",
    "ConceptSynthesizer",
    "BridgeResult",
    "GenesisReport",
    "GenesisEntry",
    "ResonanceResult",
    "EnergyProfile",
    # Perception (duyusal grounding)
    "encode_signal",
    "encode_image",
    "encode_matrix",
    "signal_autocorrelation",
    # CoreMachine (4 eksenli tekli geçiş)
    "CoreMachine",
    "UnifiedCertificate",
    "ReconstructedMeasure",
    "reconstruct_measure",
    "reconstruction_fidelity",
    "TruthCertifier",
    "TruthCertificate",
    "Confidence",
    "calibrate",
    "canonical_distance",
    "metric_distance",
    "l1_distance",
    "CollisionHunter",
    "CollisionReport",
    # Molecular Genesis
    "MolecularGenesis",
    "GenesisCandidate",
    "MolGenesisReport",
    # Quantum moments
    "FreeCumulants",
    "QuantumSignature",
    "free_entropy",
    "bounded_kappa_distance",
]
