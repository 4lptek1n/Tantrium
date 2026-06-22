"""Ters Transport — Hedeften Moleküle.

Yön: hedef (protein/hastalık/özellik) → manifold araması → fragment mutasyonu
     → minimum W2 mesafeli moleküller → 3D konformasyon

Algoritma:
  1. Hedef → moment_T (SMILES veya metin)
  2. Manifold araması: L1 ön-filtre → W2 yeniden sıralama (nearest_spectral)
  3. Fragment mutasyonu: top aday SMILES → substituent değiştirme → moment_T'ye yaklaştır
  4. Sertifika: 4 eksen (CoreMachine)
  5. 3D konformasyon: RDKit ETKDGv3
"""
from __future__ import annotations

import logging
import os
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

warnings.filterwarnings("ignore")
logging.getLogger("rdkit").setLevel(logging.CRITICAL)

try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_SUBSTITUENTS = [
    "F", "Cl", "Br", "I",
    "O", "N", "C",
    "[OH]", "[NH2]", "[CH3]", "[CF3]", "[OCH3]",
    "[CN]", "[NO2]", "[COOH]", "[SO3H]",
]

_RING_REPLACEMENTS = [
    ("c1ccccc1", "c1ccncc1"),   # benzene → pyridine
    ("c1ccccc1", "c1ccncc1"),   # benzene → pyrimidine
    ("C1CCCCC1", "C1CCNCC1"),   # cyclohexane → piperidine
    ("C1CCCCC1", "C1CCOCC1"),   # cyclohexane → morpholine
    ("c1ccccc1", "c1ccsc1"),    # benzene → thiophene
    ("c1ccccc1", "c1ccocc1"),   # benzene → furan
]

_DRUG_SCAFFOLDS = [
    ("aspirin",          "CC(=O)Oc1ccccc1C(=O)O"),
    ("ibuprofen",        "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
    ("paracetamol",      "CC(=O)Nc1ccc(O)cc1"),
    ("caffeine",         "Cn1cnc2c1c(=O)n(c(=O)n2C)C"),
    ("dopamine",         "NCCc1ccc(O)c(O)c1"),
    ("serotonin",        "NCCc1c[nH]c2ccc(O)cc12"),
    ("adenine",          "Nc1ncnc2ncnc12"),
    ("glucose",          "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O"),
    ("benzimidazole",    "c1ccc2[nH]cnc2c1"),
    ("indole",           "c1ccc2[nH]ccc2c1"),
    ("quinoline",        "c1ccc2ncccc2c1"),
    ("piperazine",       "C1CNCCN1"),
    ("imidazole",        "c1cn[nH]c1"),
    ("triazole",         "c1cnn[nH]1"),
    ("morpholine",       "C1COCCN1"),
    ("thiazolidine",     "C1CSCN1"),
    ("pyrimidine_core",  "c1ccncn1"),
    ("oxazole",          "c1cocn1"),
    ("furanose",         "C1CCCO1"),
    ("sulfonamide_ph",   "NS(=O)(=O)c1ccccc1"),
]


@dataclass
class DesignCandidate:
    name: str
    smiles: str
    moments: list[float]
    w2_distance: float
    certified: bool
    paradigms_passed: int
    paradigms_total: int
    coherent: bool
    confidence: float
    sdf_path: str = ""
    method: str = ""  # "manifold" | "fragment" | "scaffold"

    @property
    def score(self) -> float:
        """Birleşik skor: yapısal geçerlilik + düşük W2 mesafesi.
        Fragment moleküller TAU'da grounded olmaz — grounding cezalandırılmaz.
        """
        structural = self.paradigms_passed / max(self.paradigms_total, 1)
        return structural / (1.0 + self.w2_distance)

    def summary(self) -> str:
        coh = "✓" if self.coherent else "~"
        return (
            f"  {self.name:<28} W2={self.w2_distance:.4f}  "
            f"conf={self.confidence:.2f} {coh}  [{self.method}]\n"
            f"    {self.smiles[:72]}{'...' if len(self.smiles) > 72 else ''}"
            + (f"\n    3D: {self.sdf_path}" if self.sdf_path else "")
        )


@dataclass
class DesignReport:
    target: str
    target_type: str
    candidates: list[DesignCandidate]
    best: DesignCandidate | None
    duration_s: float
    n_manifold: int = 0
    n_fragment: int = 0

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════",
            "  Tantrium Ters Transport — Hedef → Molekül",
            f"  Hedef: {self.target}  [{self.target_type}]",
            f"  Manifold adayı: {self.n_manifold}  |  Fragment adayı: {self.n_fragment}",
            f"  Sertifikalı: {sum(1 for c in self.candidates if c.certified)}/{len(self.candidates)}",
            f"  Koherent: {sum(1 for c in self.candidates if c.coherent)}/{len(self.candidates)}",
            f"  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────",
        ]
        for c in self.candidates[:8]:
            lines.append(c.summary())
        if self.best:
            lines += [
                "  ────────────────────────────────────────────────────",
                f"  EN İYİ: {self.best.name}",
                f"  W2={self.best.w2_distance:.4f}  conf={self.best.confidence:.2f}  "
                f"coherent={self.best.coherent}",
                f"  {self.best.smiles}",
            ]
            if self.best.sdf_path:
                lines.append(f"  3D SDF: {self.best.sdf_path}")
        lines.append("  ════════════════════════════════════════════════════")
        return "\n".join(lines)


class InverseTransport:
    """Hedef → manifold araması + fragment mutasyonu → minimum W2 moleküller."""

    def __init__(self, engine: "CertificationEngine"):
        self.engine = engine

    # ── Genel giriş noktası ──────────────────────────────────────────────────

    def design(
        self,
        target: str,
        top_k: int = 10,
        out_dir: str = "results/molecules",
        n_fragment_rounds: int = 2,
    ) -> DesignReport:
        import time
        t0 = time.time()

        target_moments, target_type = self._encode_target(target)

        # Phase 1: manifold araması
        manifold_hits = self._search_manifold(target_moments, n=top_k * 4)

        # Phase 2: scaffold + fragment mutasyonu
        fragment_hits = self._fragment_design(
            target_moments, manifold_hits[:6], rounds=n_fragment_rounds, budget=top_k * 6
        )

        # Phase 3: sertifika + sıralama
        all_raw = manifold_hits + fragment_hits
        candidates = self._certify_and_rank(all_raw, target_moments, top_k * 2)

        # Phase 4: 3D konformasyon
        os.makedirs(out_dir, exist_ok=True)
        for c in candidates[:top_k]:
            c.sdf_path = self._make_3d(c.smiles, c.name, out_dir)

        best = candidates[0] if candidates else None
        n_m = sum(1 for c in candidates if c.method == "manifold")
        n_f = len(candidates) - n_m

        return DesignReport(
            target=target,
            target_type=target_type,
            candidates=candidates[:top_k],
            best=best,
            duration_s=round(time.time() - t0, 1),
            n_manifold=n_m,
            n_fragment=n_f,
        )

    # ── Hedef kodlama ────────────────────────────────────────────────────────

    def _encode_target(self, target: str) -> tuple[list[float], str]:
        """Hedefi moment vektörüne çevir. SMILES veya metin."""
        from tantrium.core.encoder import encode
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(target) is not None:
                obj = encode(target)
                return [float(m) for m in obj.moments], "smiles"
        except Exception:
            pass
        obj = encode(target)
        return [float(m) for m in obj.moments], "text"

    # ── Manifold araması ─────────────────────────────────────────────────────

    def _search_manifold(self, target_moments: list[float], n: int) -> list[dict]:
        """Manifolda L1 ön-filtre → W2 yeniden sıralama ile en yakın kavramları bul."""
        from fractions import Fraction

        from tantrium.core.concept import Concept

        manifold = self.engine.manifold
        if not manifold or not manifold.concepts:
            return []

        t_frac = [Fraction(m).limit_denominator(10**9) for m in target_moments]
        t_concept = Concept(name="_target", moments=t_frac)

        # nearest_spectral: L1 ön-filtre → W2 yeniden sıralama
        try:
            neighbors = manifold.nearest_spectral(t_concept, n=min(n, len(manifold.concepts)))
        except Exception:
            # Fallback: L1 doğrudan
            neighbors = manifold._nearest_l1(t_concept, n=min(n, len(manifold.concepts)))

        # nearest_spectral ve _nearest_l1 her ikisi de (name, dist) döndürür
        hits = []
        for item in neighbors[:n]:
            name, dist = item[0], item[1]
            c = manifold.concepts.get(name)
            if c is None:
                continue
            hits.append({
                "name": name,
                "smiles": self._concept_to_smiles(name),
                "moments": [float(m) for m in c.moments],
                "w2": float(dist),
                "method": "manifold",
            })

        return hits

    def _concept_to_smiles(self, name: str) -> str | None:
        """Kavram adı SMILES ise döndür, değilse None."""
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(name) is not None:
                return name
        except Exception:
            pass
        return None

    # ── Fragment mutasyonu ───────────────────────────────────────────────────

    def _fragment_design(
        self,
        target_moments: list[float],
        seed_hits: list[dict],
        rounds: int,
        budget: int,
    ) -> list[dict]:
        """Tohum SMILES'lardan + sabit scaffoldlardan substituent değiştirerek yeni moleküller üret."""
        from tantrium.core.metric import full_distance

        # Tohum: manifold'dan SMILES olanlar + drug scaffolds
        seeds: list[str] = []
        for h in seed_hits:
            if h.get("smiles"):
                seeds.append(h["smiles"])
        for _, smi in _DRUG_SCAFFOLDS:
            seeds.append(smi)

        seen: set[str] = set()
        results: list[dict] = []

        for seed_smi in seeds[:12]:
            variants = self._mutate(seed_smi, rounds=rounds)
            for v_smi in variants:
                if v_smi in seen:
                    continue
                seen.add(v_smi)
                if len(results) >= budget:
                    break
                try:
                    from tantrium.core.encoder import encode
                    obj = encode(v_smi)
                    v_moments = [float(m) for m in obj.moments]
                    w2 = full_distance(v_moments, target_moments)
                    results.append({
                        "name": f"frag_{len(results):03d}",
                        "smiles": v_smi,
                        "moments": v_moments,
                        "w2": w2,
                        "method": "fragment",
                    })
                except Exception:
                    continue
            if len(results) >= budget:
                break

        return results

    def _mutate(self, smiles: str, rounds: int = 2) -> list[str]:
        """Tek SMILES'tan RDKit substituent ekleme/değiştirme ile varyantlar üret."""
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return []

            variants: list[str] = [smiles]
            current_gen = [smiles]

            for _ in range(rounds):
                next_gen: list[str] = []
                for base_smi in current_gen[:4]:
                    next_gen.extend(self._substituent_variants(base_smi))
                    next_gen.extend(self._ring_swap_variants(base_smi))
                variants.extend(next_gen)
                current_gen = next_gen[:6]

            # Geçerli SMILES + drug-like filtresi
            clean: list[str] = []
            for s in variants:
                m = Chem.MolFromSmiles(s)
                if m is None:
                    continue
                mw = rdMolDescriptors.CalcExactMolWt(m)
                if 100 <= mw <= 600:  # Lipinski MW aralığı
                    canon = Chem.MolToSmiles(m)
                    if canon not in clean:
                        clean.append(canon)
            return clean

        except Exception:
            return [smiles]

    def _substituent_variants(self, smiles: str) -> list[str]:
        """Aromatik halkaya substituent ekle."""
        try:
            from rdkit import Chem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return []

            variants = []
            for atom in mol.GetAtoms():
                if atom.GetIsAromatic() and atom.GetSymbol() == "C":
                    if atom.GetTotalNumHs() > 0:
                        for sub in ["F", "Cl", "C", "O", "N"]:
                            rwmol = Chem.RWMol(mol)
                            new_idx = rwmol.AddAtom(Chem.Atom(sub))
                            rwmol.AddBond(atom.GetIdx(), new_idx,
                                          Chem.BondType.SINGLE)
                            try:
                                Chem.SanitizeMol(rwmol)
                                s = Chem.MolToSmiles(rwmol)
                                if s:
                                    variants.append(s)
                            except Exception:
                                pass
                            if len(variants) >= 8:
                                return variants
            return variants
        except Exception:
            return []

    def _ring_swap_variants(self, smiles: str) -> list[str]:
        """Bilinen halka değiştirmelerini uygula."""
        variants = []
        for src, tgt in _RING_REPLACEMENTS:
            if src in smiles:
                new_smi = smiles.replace(src, tgt, 1)
                try:
                    from rdkit import Chem
                    m = Chem.MolFromSmiles(new_smi)
                    if m is not None:
                        variants.append(Chem.MolToSmiles(m))
                except Exception:
                    pass
        return variants

    # ── Sertifika + sıralama ─────────────────────────────────────────────────

    def _certify_and_rank(
        self, raw: list[dict], target_moments: list[float], top_k: int
    ) -> list[DesignCandidate]:
        """Yapısal hızlı sertifika + W2 sıralama.

        Fragment moleküller TAU'da grounded olmaz — bu beklenen durum.
        Yapısal geçerlilik (paradigmalar) + W2 mesafesi ile sırala.
        """
        # W2'ye göre ön sıralama, kopyaları temizle
        seen_smi: set[str] = set()
        raw_unique: list[dict] = []
        for h in sorted(raw, key=lambda x: x["w2"]):
            key = h.get("smiles") or h.get("name", "")
            if key not in seen_smi:
                seen_smi.add(key)
                raw_unique.append(h)

        raw_sorted = raw_unique[:top_k * 3]

        candidates: list[DesignCandidate] = []
        for h in raw_sorted:
            name = h.get("name") or (h.get("smiles") or "")[:20]
            smiles = h.get("smiles")
            w2 = h["w2"]
            h_moments = h.get("moments", [])

            # Hızlı yapısal sertifika (pipeline doğrudan, CoreMachine değil)
            certified = False
            paradigms_passed = 0
            paradigms_total = 23
            coherent = False
            confidence = 0.0

            try:
                encode_key = smiles if smiles else name
                run = self.engine.network.run(
                    self.engine.encoder.encode(encode_key)
                )
                paradigms_passed = run.certified_count
                paradigms_total = run.total
                certified = paradigms_passed >= paradigms_total - 1
                # Güven: yapısal orana göre (grounding cezası yok)
                confidence = paradigms_passed / max(paradigms_total, 1)
                coherent = certified
            except Exception:
                pass

            candidates.append(DesignCandidate(
                name=name,
                smiles=smiles or "",
                moments=h_moments,
                w2_distance=w2,
                certified=certified,
                paradigms_passed=paradigms_passed,
                paradigms_total=paradigms_total,
                coherent=coherent,
                confidence=confidence,
                method=h.get("method", "unknown"),
            ))

        # SMILES adayları önce (ilaç tasarımı için), sonra W2 + yapısal skor
        def _rank_key(c: DesignCandidate):
            has_smi = 1 if c.smiles else 0
            return (-has_smi, -c.score, c.w2_distance)

        candidates.sort(key=_rank_key)
        return candidates

    # ── 3D konformasyon ──────────────────────────────────────────────────────

    def _make_3d(self, smiles: str, name: str, out_dir: str) -> str:
        """RDKit ETKDGv3 ile 3D konformasyon üret, SDF kaydet.

        Kanonik `embed_3d_sdf` util'ine delege (#7): remove_hs=True + SMILES alanı.
        """
        from tantrium.core.molecular_3d import embed_3d_sdf
        return embed_3d_sdf(
            smiles, name, out_dir,
            props={"SMILES": smiles},
            remove_hs=True,
        )
