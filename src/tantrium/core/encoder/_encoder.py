"""The universal encoder: any input → CodexObject via spectral moments.

Domain-blind. It never asks "what kind of thing is this?" — it only asks
"what is the spectral distribution of this thing's matrix?". That question has
a universal answer for every input that can be represented as a non-negative
matrix — which is everything.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from tantrium.core.paradigms import CertifiableObject as CodexObject

from ._linalg import _gram, _sequence_to_hankel_matrix, _spectral_moments
from ._text import (
    _dict_to_adjacency_matrix,
    _is_valid_smiles,
    _numbers_to_matrix,
    _smiles_full_eigenvalues,
    _smiles_molecular_moments,
    _text_to_bigram_matrix,
    _text_to_signature_moments,
    _tokens_to_cooccurrence_matrix,
    _try_power_moments,
)


class UniversalEncoder:
    """Domain-blind encoder: any input → CodexObject via spectral moments.

    The encoder never asks "what kind of thing is this?"
    It only asks "what is the spectral distribution of this thing's matrix?"

    That question has a universal answer for every input that can be
    represented as a non-negative matrix — which is everything.
    """

    def __init__(self, num_moments: int = 8) -> None:
        self.num_moments = num_moments

    def encode(self, input: Any, name: str | None = None) -> CodexObject:
        """Encode any input to a CodexObject with auto-extracted structure.

        Computes spectral moments AND auto-populates structure fields
        for as many paradigms as possible from the raw input alone.
        No domain knowledge required.

        Uzun sayısal diziler için hızlı yol: μ_k = ort(x^k) doğrudan float'ta
        hesaplanır, rasyonelleştirilir. Exact matris üssü (G^k) uzun dizilerde
        Fraction paydalarını patlatır (yüzlerce basamak) — bu yol onu atlar.
        Yapı çıkarımı için küçük temsilî matris kullanılır.
        """
        obj_name = name or _infer_name(input)

        fast_moments = _try_power_moments(input, self.num_moments)
        if fast_moments is not None:
            moments = fast_moments
            # Yapı çıkarımı için momentlerden küçük Hankel matrisi (tam diziyi
            # yeniden işleme — payda patlamasını ve O(n³)'ü tamamen atla)
            A = _sequence_to_hankel_matrix(moments)
            G = _gram(A)
            structure = self._extract_structure(input, A, G, moments)
            structure.update({
                "encoder": "universal_spectral",
                "matrix_size": len(A),
                "input_type": type(input).__name__,
                "num_moments": self.num_moments,
                "moment_path": "power_moments_fast",
            })
            return CodexObject(name=obj_name, moments=moments, structure=structure)

        # Saf-matematik makinesi: girdi sayı/dizi/matris/dict veya molekül (SMILES).
        # Dil/kod/biyo-dizi modaliteleri kaldırıldı. Bir string ya geçerli SMILES'tir
        # (→ _to_matrix bigram), ya da deterministik imza-momentine hash'lenir (math,
        # yakınlık/anlam YOK). Metin-imza yolu: pozisyon+codepoint, [0,1] Hausdorff.
        if isinstance(input, str) and len(input) > 1 and not _is_valid_smiles(input):
            sig_moments = _text_to_signature_moments(input, self.num_moments)
            if sig_moments is not None:
                A = _sequence_to_hankel_matrix(sig_moments)
                G = _gram(A)
                structure = self._extract_structure(input, A, G, sig_moments)
                structure.update({
                    "encoder": "text_signature",
                    "matrix_size": len(A),
                    "input_type": type(input).__name__,
                    "num_moments": self.num_moments,
                    "moment_path": "text_signature",
                })
                return CodexObject(name=obj_name, moments=sig_moments, structure=structure)

        A = self._to_matrix(input)
        G = _gram(A)
        moments = _spectral_moments(A, self.num_moments)
        structure = self._extract_structure(input, A, G, moments)
        structure.update({
            "encoder": "universal_spectral",
            "matrix_size": len(A),
            "input_type": type(input).__name__,
            "num_moments": self.num_moments,
        })
        return CodexObject(name=obj_name, moments=moments, structure=structure)

    def _extract_structure(
        self,
        input: Any,
        A: list[list[Fraction]],
        G: list[list[Fraction]],
        moments: list[Fraction],
    ) -> dict:
        """Auto-extract structural metadata for all 22 paradigms.

        Delegates to the L0–L7 pipeline in tantrium.core.pipeline.
        Each stage does exactly its own mathematical transformation and
        consumes the previous stage's output. Encoder only provides raw
        matrix A and moments — the pipeline does the rest.
        """
        from tantrium.core.pipeline import run_pipeline
        state = run_pipeline(input, A, G, moments)
        try:
            from tantrium.core.quantum_moments import FreeCumulants
            state["free_cumulants"] = FreeCumulants.from_moments(
                [float(m) for m in moments]
            ).k
        except Exception:
            pass
        # RH sertifika bundle: tce-collapse'in TÜM moment-RH matematiği tek bütünde
        # (τ/pivot/cross-ratio/Stieltjes/kümülant/Λ/rank + Hausdorff + Turán + yarı-daire
        # + mühür). 8 kanonik moment bozulmaz; 16-derinlik genişletilmiş momentten. Yola
        # uygun: numeric→power, matris→spektral. heavy=False (free_entropy hot-path'te atlanır).
        try:
            from tantrium.core.rh_certificate import certify_rh
            ext = _try_power_moments(input, 16)
            if ext is None:
                ext = _spectral_moments(A, 16)
            cert = certify_rh(ext, name=str(getattr(self, "_last_name", "rh")), heavy=False)
            state["rh"] = cert.as_dict()
            state["rh_criteria"] = cert.criteria.as_dict()  # geriye uyum
        except Exception:
            pass
        return state

    def _to_matrix(self, input: Any) -> list[list[Fraction]]:
        if isinstance(input, (list, tuple)) and input:
            first = input[0]
            if isinstance(first, Fraction):
                return _sequence_to_hankel_matrix(list(input))
            if isinstance(first, (int, float)):
                return _numbers_to_matrix(input)
            if isinstance(first, str):
                return _tokens_to_cooccurrence_matrix(list(input))
        if isinstance(input, str):
            if len(input) <= 1:
                return [[Fraction(1)]]
            return _text_to_bigram_matrix(input, label_aware=True)
        if isinstance(input, dict):
            return _dict_to_adjacency_matrix(input)
        if isinstance(input, (int, float)):
            seq = [Fraction(input).limit_denominator(10 ** 9)]
            return _numbers_to_matrix(seq)
        if isinstance(input, Fraction):
            return _numbers_to_matrix([input])
        return _text_to_bigram_matrix(str(input), label_aware=True)

    def encode_batch(self, inputs: list[Any], names: list[str] | None = None) -> list[CodexObject]:
        """Encode multiple inputs in one call."""
        if names is None:
            names = [None] * len(inputs)
        return [self.encode(inp, nm) for inp, nm in zip(inputs, names)]

    def encode_adaptive(
        self,
        input: Any,
        name: str | None = None,
        base_depth: int = 8,
        max_depth: int = 16,
        fidelity_target: float = 0.999,
    ) -> CodexObject:
        """Adaptif derinlikli kodlama — belirsiz girdide tohumu derinleştir.

        8 sabit moment darboğazdır: iki farklı yapı 8'de çakışabilir.
        Bu metod önce base_depth moment hesaplar, ölçünün NE KADAR İYİ
        SABİTLENDİĞİNİ ölçer (rekonstrüksiyon sadakati). Sadakat düşükse
        — yani momentler ölçüyü zayıf belirliyorsa — derinliği artırır.

        Sinyal: reconstruction_fidelity (momentlerden ölçüyü geri kurup
        momentleri yeniden hesapla, hata ne kadar küçükse o kadar belirli).

        Sonuç structure["moment_depth"] kullanılan gerçek derinliği taşır.
        """
        from tantrium.core.reconstruct import reconstruct_measure

        depth = base_depth
        obj = self.encode(input, name) if base_depth == self.num_moments \
            else UniversalEncoder(base_depth).encode(input, name)

        rec = reconstruct_measure(obj.moments)
        # İyi belirliyse derinleştirme gerekmiyor
        import math
        fidelity = math.exp(-rec.reconstruction_error * 100.0)

        while fidelity < fidelity_target and depth < max_depth:
            depth = min(max_depth, depth + 4)
            obj = UniversalEncoder(depth).encode(input, name)
            rec = reconstruct_measure(obj.moments)
            fidelity = math.exp(-rec.reconstruction_error * 100.0)

        obj.structure["moment_depth"] = depth
        obj.structure["reconstruction_fidelity"] = round(fidelity, 6)
        obj.structure["measure_rank"] = rec.rank
        return obj


def _infer_name(input: Any) -> str:
    if isinstance(input, str):
        return input[:40].replace("\n", " ")
    if isinstance(input, dict) and "name" in input:
        return str(input["name"])[:40]
    return f"{type(input).__name__}_{id(input) % 10000}"


# ─── Convenience ────────────────────────────────────────────────────────────

_DEFAULT_ENCODER = UniversalEncoder()


def encode(input: Any, name: str | None = None, num_moments: int = 8) -> CodexObject:
    """One-call universal encoding. No domain knowledge required."""
    if num_moments != 8:
        return UniversalEncoder(num_moments).encode(input, name)
    return _DEFAULT_ENCODER.encode(input, name)


def encode_smiles(smiles: str, name: str | None = None, num_moments: int = 8) -> CodexObject:
    """SMILES → Hausdorff descriptor moments → Gram → CodexObject.

    12 RDKit physicochemical descriptors (MW, logP, HBA, HBD, TPSA, RotBonds,
    Rings, AroRings, HeavyAtoms, CSP3, AliRings, Heteroatoms) each normalized
    to [0,1] and treated as atom positions on the real line.

    Power moments m_k = mean(d_i^k) form a valid Hausdorff moment sequence
    → Hankel PSD guaranteed → ALEPH always passes. The moment distribution
    captures pharmacological class: NSAIDs, kinase inhibitors, and antibiotics
    each occupy distinct regions of moment space.
    """
    encoder = _DEFAULT_ENCODER if num_moments == 8 else UniversalEncoder(num_moments)
    moments = _smiles_molecular_moments(smiles, num_moments)
    if moments is None:
        # RDKit unavailable or invalid SMILES — fall back to text encoding
        return encoder.encode(smiles, name)
    # Build Hankel from valid Hausdorff moments → Gram → structure metadata
    A = _sequence_to_hankel_matrix(moments)
    G = _gram(A)
    structure = encoder._extract_structure(smiles, A, G, moments)
    # Override eigenvalues with actual n×n molecular graph spectrum so that
    # CertifiedTransport cells reflect genuine molecular topology differences.
    mol_eigs = _smiles_full_eigenvalues(smiles)
    if mol_eigs:
        structure["eigenvalues"] = mol_eigs
        structure["eigenvalue_source"] = "molecular_graph"
    structure.update({
        "encoder":    "rdkit_descriptors",
        "smiles":     smiles[:100],
        "input_type": "smiles",
    })
    return CodexObject(name=name or smiles[:40], moments=moments, structure=structure)
