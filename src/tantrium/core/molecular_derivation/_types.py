"""Moleküler Genesis — veri tipleri ve modül sabitleri.

GenesisCandidate / SimStep / SimulationReport / GenesisReport dataclass'ları
ve atom/bağ ekleme sabitleri.
"""
from __future__ import annotations

from dataclasses import dataclass

# Ekleme adayları: (atom_sembolü, atomik_numara)
_ATOMS = [
    ("C", 6), ("N", 7), ("O", 8), ("S", 16), ("F", 9), ("Cl", 17),
]

# Bağ tipleri denenecek
_BONDS = ["SINGLE", "DOUBLE", "AROMATIC"]


@dataclass
class GenesisCandidate:
    smiles: str
    moments: list[float]
    w2: float
    paradigms_passed: int
    paradigms_total: int
    n_atoms: int
    steps: int  # kaç adımda üretildi


@dataclass
class SimStep:
    """Evren simülasyonunda tek bir transport-sertifikalı ilerleme adımı."""
    smiles: str
    n_atoms: int
    certified: bool          # dyadic ∧ sturm — tam gerçek adım
    dyadic: bool
    sturm: bool
    zeta: float              # Riemann ζ ailesine derinlik
    cost: float


@dataclass
class SimulationReport:
    """Makinenin kendisini çalıştırarak dizdiği molekül soyu.

    Hafıza araması yok — her adım CertifiedTransport ile yargılandı.
    """
    seed: str
    lineage: list[SimStep]                 # tohum→son: ilerleme yolu
    frontier: list[SimStep]                # son beam (sürdürülebilir uçlar)
    best: SimStep | None                   # en düşük-ζ sertifikalı uç
    certified_steps: int                   # kaç adım dyadic∧sturm geçti
    total_steps: int
    duration_s: float

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium Evren Simülasyonu — Transport ile Molekül Dizilimi",
            f"  Tohum: {self.seed}  →  {len(self.lineage)} adım soy",
            f"  Sertifikalı adım (dyadic∧sturm): {self.certified_steps}/{self.total_steps}",
            f"  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, s in enumerate(self.lineage):
            mark = "✓" if s.certified else ("~" if s.sturm else "✗")
            lines.append(
                f"  {i:2}. {mark} {s.smiles:<32} "
                f"[{s.n_atoms} atom]  ζ={s.zeta:.3f}  "
                f"dyadic={'✓' if s.dyadic else '·'} sturm={'✓' if s.sturm else '·'}"
            )
        if self.best:
            lines += [
                "  ────────────────────────────────────────────────────────────",
                f"  EN DERİN SERTİFİKALI UÇ: {self.best.smiles}  (ζ={self.best.zeta:.4f})",
            ]
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)


@dataclass
class GenesisReport:
    target: str
    target_moments: list[float]
    candidates: list[GenesisCandidate]
    best: GenesisCandidate | None
    duration_s: float
    total_steps: int

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium Moleküler Genesis — Saf Türetim",
            f"  Hedef: {self.target}",
            f"  Toplam adım: {self.total_steps}  |  Aday: {len(self.candidates)}",
            f"  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, c in enumerate(self.candidates[:8]):
            cert = "✓" if c.paradigms_passed >= c.paradigms_total - 1 else "~"
            lines.append(
                f"  {i+1:2}. {cert} W2={c.w2:.4f}  "
                f"[{c.paradigms_passed}/{c.paradigms_total}]  "
                f"{c.n_atoms} atom  {c.steps} adım"
            )
            lines.append(f"       {c.smiles[:72]}")
        if self.best:
            lines += [
                "  ────────────────────────────────────────────────────────────",
                f"  EN İYİ:  W2={self.best.w2:.4f}  "
                f"[{self.best.paradigms_passed}/{self.best.paradigms_total}]",
                f"  {self.best.smiles}",
            ]
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)
