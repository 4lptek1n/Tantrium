"""Tantrium: structure-first symbolic certification engine.

Pure, stateless mathematics. Input (number / matrix / molecule / signal-as-number)
→ spectral moments → 23-paradigm certification → certified transport / reconstruction
/ law discovery. No language layer, no learned graph, no autonomous growth — only
the RH-derived positivity machine and the domains that reduce to it.
"""
from tantrium.ai import AI, AskResult, MolResult, DiscoverResult, DesignResult
from tantrium.core.engine import CertificationEngine
from tantrium.core.unified import CoreMachine, UnifiedCertificate
from tantrium.core.reconstruct import ReconstructedMeasure, reconstruct_measure, reconstruction_fidelity
from tantrium.core.truth import TruthCertifier, TruthCertificate
from tantrium.core.confidence import Confidence, calibrate
from tantrium.core.metric import canonical_distance, l1_distance, distance as metric_distance
from tantrium.core.collision import CollisionHunter, CollisionReport
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.encoder import UniversalEncoder, encode, encode_smiles
from tantrium.core.concept import Concept, moment_distance
from tantrium.core.rh_criteria import rh_criteria, RHCriteria, criteria_distance
from tantrium.core.rh_certificate import certify_rh, RHCertificate, hausdorff
from tantrium.core.jensen import laguerre_polya_test, is_hyperbolic, turan, JensenReport
from tantrium.core.free_probability import (
    free_entropy, r_transform, free_convolution, semicircle_distance,
)
from tantrium.core.verifier import seal, verify, adversarial_control, tamper_test
from tantrium.core.bezoutian import (
    analyze as bezoutian_analyze, lah_pivot_reference, staircase_top_coeff, BezoutianReport,
)
from tantrium.core.transport import CertifiedTransport, TransportCertificate, TransportRanking
from tantrium.proof.certificate import Cell, Certificate, TransportEdge
from tantrium.proof.dyadic_flow import solve_greedy, FlowPolicy
from tantrium.domains.spectral import SpectralMeasure, gram_spectrum, spectral_distance, dna_measure, moments_to_spectral
from tantrium.core.inverse import InverseTransport, DesignCandidate, DesignReport
from tantrium.core.molecular_space import MolecularSpace, MolPoint, ArrangementResult, MorphResult
from tantrium.core.molecular_genesis import MolecularGenesis, GenesisCandidate, GenesisReport as MolGenesisReport
from tantrium.core.quantum_moments import (
    FreeCumulants,
    QuantumSignature,
    bounded_kappa_distance,
    free_entropy,
)

__all__ = [
    # SDK
    "AI",
    "AskResult",
    "MolResult",
    "DiscoverResult",
    "DesignResult",
    # Certification core
    "CertificationEngine",
    "CertificationPipeline",
    "CertificationRun",
    "UniversalEncoder",
    "encode",
    "encode_smiles",
    "Concept",
    "moment_distance",
    "rh_criteria",
    "RHCriteria",
    "criteria_distance",
    "certify_rh",
    "RHCertificate",
    "hausdorff",
    "laguerre_polya_test",
    "is_hyperbolic",
    "turan",
    "JensenReport",
    "free_entropy",
    "r_transform",
    "free_convolution",
    "semicircle_distance",
    "seal",
    "verify",
    "adversarial_control",
    "tamper_test",
    "bezoutian_analyze",
    "lah_pivot_reference",
    "staircase_top_coeff",
    "BezoutianReport",
    # Transport
    "CertifiedTransport",
    "TransportCertificate",
    "TransportRanking",
    # Proof primitives
    "Cell",
    "Certificate",
    "TransportEdge",
    "solve_greedy",
    "FlowPolicy",
    # Spectral / domains
    "SpectralMeasure",
    "gram_spectrum",
    "spectral_distance",
    "dna_measure",
    "moments_to_spectral",
    # Molecular (math domains)
    "InverseTransport",
    "DesignCandidate",
    "DesignReport",
    "MolecularSpace",
    "MolPoint",
    "ArrangementResult",
    "MorphResult",
    "MolecularGenesis",
    "GenesisCandidate",
    "MolGenesisReport",
    # CoreMachine (4-axis single pass)
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
    # Quantum moments (free probability)
    "FreeCumulants",
    "QuantumSignature",
    "free_entropy",
    "bounded_kappa_distance",
]
