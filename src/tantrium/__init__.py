"""Tantrium: structure-first symbolic certification engine.

Pure, stateless mathematics. Input (number / matrix / molecule / signal-as-number)
→ spectral moments → 23-paradigm certification → certified transport / reconstruction
/ law discovery. No language layer, no learned graph, no autonomous growth — only
the RH-derived positivity machine and the domains that reduce to it.
"""
from tantrium.ai import AI, AskResult, DesignResult, DiscoverResult, MolResult
from tantrium.core.bezoutian import (
    BezoutianReport,
    lah_pivot_reference,
    staircase_top_coeff,
)
from tantrium.core.bezoutian import (
    analyze as bezoutian_analyze,
)
from tantrium.core.collision import CollisionHunter, CollisionReport
from tantrium.core.concept import Concept, moment_distance
from tantrium.core.confidence import Confidence, calibrate
from tantrium.core.encoder import UniversalEncoder, encode, encode_smiles
from tantrium.core.engine import CertificationEngine
from tantrium.core.fixed_point import SelfReferenceResult, self_map, self_reference_orbit
from tantrium.core.free_probability import (
    free_convolution,
    free_entropy,
    r_transform,
    semicircle_distance,
)
from tantrium.core.interaction import Interaction, interact
from tantrium.core.inverse import DesignCandidate, DesignReport, InverseTransport
from tantrium.core.jensen import JensenReport, is_hyperbolic, laguerre_polya_test, turan
from tantrium.core.metric import (
    canonical_distance,
    certificate_distance,
    certificate_vector,
    full_distance,
    l1_distance,
    paradigm_distance,
    paradigm_signature,
)
from tantrium.core.metric import distance as metric_distance
from tantrium.core.molecular_derivation import GenesisCandidate, MolecularGenesis
from tantrium.core.molecular_derivation import GenesisReport as MolGenesisReport
from tantrium.core.molecular_space import ArrangementResult, MolecularSpace, MolPoint, MorphResult
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.operator import to_eig, to_gram, to_matrix
from tantrium.core.quantum_moments import (
    FreeCumulants,
    QuantumSignature,
    bounded_kappa_distance,
)
from tantrium.core.reconstruct import (
    ReconstructedMeasure,
    reconstruct_measure,
    reconstruction_fidelity,
)
from tantrium.core.relation import Relation, relate
from tantrium.core.rh_certificate import RHCertificate, certify_rh, hausdorff
from tantrium.core.rh_criteria import RHCriteria, criteria_distance, rh_criteria
from tantrium.core.spectral_class import (
    SpectralClass,
    classify_spectrum,
    spectral_class,
)
from tantrium.core.spectral_flow import SpectralFlow, flow_between, spectral_flow
from tantrium.core.spectral_geometry import SpectralGeometry, spectral_geometry
from tantrium.core.spectral_reading import SpectralReading
from tantrium.core.spectral_reading import read as spectral_reading
from tantrium.core.transport import CertifiedTransport, TransportCertificate, TransportRanking
from tantrium.core.truth import TruthCertificate, TruthCertifier
from tantrium.core.unified import CoreMachine, UnifiedCertificate
from tantrium.core.verifier import adversarial_control, seal, tamper_test, verify
from tantrium.core.zeta_operator import (
    HilbertPolyaCertificate,
    ZetaOperatorProbe,
    berry_keating_zeros,
    certify_hilbert_polya,
    compute_zeros,
    probe_zeta_operator,
    riemann_siegel_z,
    zeta_operator_matrix,
    zeta_operator_zeros,
)
from tantrium.cosmos import Epoch, Lifecycle, run_cosmos
from tantrium.domains.spectral import (
    SpectralMeasure,
    dna_measure,
    gram_spectrum,
    moments_to_spectral,
    spectral_distance,
)
from tantrium.proof.certificate import Cell, Certificate, TransportEdge
from tantrium.proof.dyadic_flow import FlowPolicy, solve_greedy
from tantrium.universe import Universe, universe

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
    "spectral_class",
    "classify_spectrum",
    "SpectralClass",
    "spectral_reading",
    "SpectralReading",
    "spectral_flow",
    "flow_between",
    "SpectralFlow",
    "certify_rh",
    "RHCertificate",
    "hausdorff",
    "self_reference_orbit",
    "self_map",
    "SelfReferenceResult",
    "run_cosmos",
    "Lifecycle",
    "Epoch",
    "universe",
    "Universe",
    "interact",
    "Interaction",
    "relate",
    "Relation",
    "to_matrix",
    "to_gram",
    "to_eig",
    "spectral_geometry",
    "SpectralGeometry",
    "probe_zeta_operator",
    "ZetaOperatorProbe",
    "berry_keating_zeros",
    "zeta_operator_zeros",
    "zeta_operator_matrix",
    "compute_zeros",
    "riemann_siegel_z",
    "certify_hilbert_polya",
    "HilbertPolyaCertificate",
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
    "certificate_vector",
    "certificate_distance",
    "full_distance",
    "paradigm_distance",
    "paradigm_signature",
    "CollisionHunter",
    "CollisionReport",
    # Quantum moments (free probability)
    "FreeCumulants",
    "QuantumSignature",
    "bounded_kappa_distance",
]
