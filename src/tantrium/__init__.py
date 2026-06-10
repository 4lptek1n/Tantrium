"""Tantrium: structure-first symbolic discovery framework."""
from tantrium.ai import AI, AskResult, MolResult, GenResult, ReasonResult, DiscoverResult, DesignResult
from tantrium.core.engine import CertificationEngine
from tantrium.core.unified import CoreMachine, UnifiedCertificate
from tantrium.core.reconstruct import ReconstructedMeasure, reconstruct_measure, reconstruction_fidelity
from tantrium.core.truth import TruthCertifier, TruthCertificate
from tantrium.core.confidence import Confidence, calibrate
from tantrium.core.metric import canonical_distance, l1_distance, distance as metric_distance
from tantrium.core.collision import CollisionHunter, CollisionReport
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.encoder import UniversalEncoder, encode, encode_smiles
from tantrium.core.semantic import Concept, SemanticManifold
from tantrium.core.transport import CertifiedTransport, TransportCertificate, TransportRanking
from tantrium.proof.certificate import Cell, Certificate, TransportEdge
from tantrium.proof.dyadic_flow import solve_greedy, FlowPolicy
from tantrium.graph.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeEdge
from tantrium.graph.memory import SessionMemory, Turn
from tantrium.research.proof_loop import ProofLoop, LoopReport, LoopCycle
from tantrium.reasoning.thinker import ThinkingResult, ThinkingLevel
from tantrium.reasoning.generalization import DerivedConcept, HankelGeneralizer
from tantrium.reasoning.necessity import NecessityReport, NecessaryEdge, ManifoldGap
from tantrium.reasoning.reasoner import ChainStep, ReasoningResult, GraphReasoner
from tantrium.reasoning.planner import Plan, PlanStep, Planner
from tantrium.research.autonomous import Observation, AutonomousObserver
from tantrium.research.explorer import ExplorationObjective, ExplorationResult
from tantrium.research.goal import Goal, GoalManifold
from tantrium.research.actor import Action, ActionResult
from tantrium.research.ingest import IngestBatch, IngestReport, DataIngestor
from tantrium.research.researcher import ResearchCycle, ResearchReport, AutonomousResearcher
from tantrium.language.generator import GeneratedStep, GenerationResult, CertifiedGenerator
from tantrium.language.speaker import CertifiedStatement, Speaker
from tantrium.domains.spectral import SpectralMeasure, gram_spectrum, spectral_distance, dna_measure, moments_to_spectral
from tantrium.meta.paradigm import MetaParadigm, UniversalRule, ParadigmMoment, SelfCertResult
from tantrium.meta.topology import MomentTopology, MathRegion
from tantrium.meta.vision import CosmicVision, CosmicFrame
from tantrium.meta.self_model import SelfModel, SelfReflection
from tantrium.meta.synthesis import (
    ConceptSynthesizer, BridgeResult, GenesisReport, GenesisEntry,
    ResonanceResult, EnergyProfile,
)
from tantrium.perception import (
    encode_signal, encode_image, encode_matrix, signal_autocorrelation,
)
from tantrium.core.inverse import InverseTransport, DesignCandidate, DesignReport
from tantrium.core.molecular_space import MolecularSpace, MolPoint, ArrangementResult, MorphResult
from tantrium.core.molecular_genesis import MolecularGenesis, GenesisCandidate, GenesisReport as MolGenesisReport
from tantrium.core.quantum_moments import FreeCumulants, QuantumSignature

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
    "Observation",
    "AutonomousObserver",
    "ExplorationObjective",
    "ExplorationResult",
    "Goal",
    "GoalManifold",
    "Action",
    "ActionResult",
    "IngestBatch",
    "IngestReport",
    "DataIngestor",
    "ResearchCycle",
    "ResearchReport",
    "AutonomousResearcher",
    # Reasoning
    "ThinkingResult",
    "ThinkingLevel",
    "NecessityReport",
    "NecessaryEdge",
    "ManifoldGap",
    "DerivedConcept",
    "HankelGeneralizer",
    "ChainStep",
    "ReasoningResult",
    "GraphReasoner",
    "Plan",
    "PlanStep",
    "Planner",
    # Language
    "GeneratedStep",
    "GenerationResult",
    "CertifiedGenerator",
    "CertifiedStatement",
    "Speaker",
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
]
