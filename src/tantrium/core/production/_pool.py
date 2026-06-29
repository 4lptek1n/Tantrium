"""Çok-stratejili aday havuzu mixin — genesis/scaffold/inverse/morph/de-novo + refine.

_build_pool / _refine / _decompose_combination / _inject_manifold.
_PRIMITIVES sabitini _types'tan alır; geri kalan tüm yardımcılar ProductionEngine'de.
"""
from __future__ import annotations

from ._types import _PRIMITIVES


class _PoolMixin:
    # ── Çok-stratejili havuz ──────────────────────────────────────────────

    def _build_pool(self, target: str, mu_req: list[float],
                    profiles: list[list[float]], max_steps: int,
                    beam_width: int) -> list[str]:
        """Stratejilerden aday havuzu: genesis · scaffold · inverse · morph · doğrudan ·
        de-novo-reconstruction (özdeğer-spektrumundan inşa) · kuantum-köprü scaffold."""
        seen: set[str] = set()
        pool: list[str] = []

        def _add(smi: str) -> None:
            if smi and smi not in seen and self._chemically_stable(smi):
                seen.add(smi)
                pool.append(smi)

        # 1. Genesis (birincil): Sturm geçidi içinde büyü
        try:
            from tantrium.core.molecular_derivation import MolecularGenesis
            rep = MolecularGenesis(self.engine).simulate(
                seeds=_PRIMITIVES, max_steps=max_steps, beam_width=beam_width,
                toward_profile=profiles)
            for s in rep.frontier + list(reversed(rep.lineage)):
                _add(s.smiles)
        except Exception:
            pass

        # 2. Scaffold-hybrid (kinaz kütüphanesi)
        try:
            from tantrium.domains.generator import MoleculeGenerator
            gen = MoleculeGenerator(self.engine)
            for smi in gen.generate(target, n=beam_width * 2):
                _add(smi if isinstance(smi, str) else getattr(smi, "smiles", ""))
        except Exception:
            pass

        # 3. Inverse-transport (fragment mutasyonu)
        try:
            from tantrium.core.inverse import InverseTransport
            inv = InverseTransport(self.engine)
            cands = inv.design(target, top_k=beam_width)
            for c in (cands if isinstance(cands, list) else getattr(cands, "candidates", [])):
                _add(c if isinstance(c, str) else getattr(c, "smiles", ""))
        except Exception:
            pass

        # 4. Morph (ilaç kütüphanesi arası ara noktalar)
        try:
            from tantrium.core.molecular_space import DRUG_LIBRARY, MolecularSpace
            ms = MolecularSpace(self.engine)
            seeds_mol = [smi for _, smi, _ in DRUG_LIBRARY[:4]]
            for src in seeds_mol[:2]:
                for tgt in seeds_mol[2:4]:
                    path = ms.morph(src, tgt, steps=4)
                    for pt in getattr(path, "path", []):
                        _add(getattr(pt, "smiles", ""))
        except Exception:
            pass

        # 5. Doğrudan: SMILES hedefin kendi ligandları
        if self._is_smiles(target):
            _add(target)
        for _, smi in self._reference_ligands(target)[:4]:
            _add(smi)

        # Stages 6-7 = DE-NOVO yedek hattı (kanıtlanmış 1-5 yetmezse). Her zaman havuza
        # girer ama AYRI işaretlenir: sıralamada kanıtlanmış aday ÖNCE gelir (proven-first),
        # böylece druggable hedefte reconstruction'ın saf moment-eşleştiricileri (küçük-
        # molekül dejenerasyonu) kanıtlanmış ilacı GEÇEMEZ. De-novo yalnız başka coherent
        # aday yoksa kazanır = tam ihtiyaç olan yerde (undruggable) güç açılır. Defter ilkesi:
        # gerçek ayrımı koru, en-küçük-ortak-payda DEĞİL.
        denovo: set[str] = set()

        def _add_denovo(smi: str) -> None:
            before = len(pool)
            _add(smi)
            if len(pool) > before:        # gerçekten eklendiyse de-novo olarak işaretle
                denovo.add(pool[-1])

        # 6. De novo reconstruction: hedefin moment-imzasından özdeğer-ölçüsünü GERİ KUR
        #    (Gauss kuadratür/Prony) → temizlenmiş moment → genesis o ölçüye inşa eder.
        #    LİGANDSIZ hedefin ASIL gücü: bilinen ilaç YOK, yalnız hedefin matematiği.
        try:
            from tantrium.core.reconstruct import reconstruct_measure
            rec = reconstruct_measure(mu_req, max_atoms=4)
            if rec.support and rec.reconstruction_error < 0.5:
                mu_clean = [float(m) for m in rec.reconstructed_moments][:8]
                from tantrium.core.molecular_derivation import MolecularGenesis
                rep = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES, max_steps=max_steps, beam_width=beam_width,
                    toward_profile=[mu_clean])
                for s in rep.frontier + list(reversed(rep.lineage)):
                    _add_denovo(s.smiles)
        except Exception:
            pass

        # 7. Kuantum köprü scaffold'u: hedefe κ-DOLANIK (klasik-uzak) çapraz-domain
        #    kavramların molekülleri. Gizli matematiksel bağ → naif benzerliğin
        #    göremediği yeni iskele. (F8 "elma-DNA × Fibonacci" ilkesi üretimde.)
        try:
            mani = getattr(self.engine, "manifold", None)
            if mani is not None and hasattr(mani, "quantum_bridges"):
                for bname, _qd in mani.quantum_bridges(target, top_k=6):
                    if bname.startswith("⟨"):       # genesis yapay köprüsü — atla
                        continue
                    if self._is_smiles(bname):
                        _add_denovo(bname)
                    else:
                        for _, smi in self._reference_ligands(bname)[:2]:
                            _add_denovo(smi)
        except Exception:
            pass

        self._denovo_smiles = denovo     # produce() sıralaması proven-first için okur
        return pool

    def _refine(self, scored: list[dict], mu_req: list[float],
                profiles: list[list[float]], max_steps: int,
                beam_width: int) -> list[str]:
        """Kapanış kalıntısı gradyanıyla yeniden üret (fixed-point refine adımı)."""
        if not scored:
            return []
        best_smi = scored[0]["smiles"]
        mu_best = self._encode(best_smi)
        if not mu_best:
            return []
        # Kalıntı = gerekli - mevcut (yeni gradyan yönü)
        [mu_req[i] - mu_best[i] if i < len(mu_best) else mu_req[i]
                    for i in range(len(mu_req))]
        new_target = [0.5 * (mu_best[i] + mu_req[i]) for i in range(
            min(len(mu_best), len(mu_req)))]
        try:
            from tantrium.core.molecular_derivation import MolecularGenesis
            rep = MolecularGenesis(self.engine).simulate(
                seeds=[best_smi] + _PRIMITIVES[:3],
                max_steps=max(4, max_steps // 2), beam_width=beam_width,
                toward_profile=[new_target])
            result = []
            for s in rep.frontier + list(reversed(rep.lineage)):
                if self._chemically_stable(s.smiles):
                    result.append(s.smiles)
            return result
        except Exception:
            return []

    def _decompose_combination(self, mu_req: list[float],
                               profiles: list[list[float]],
                               max_steps: int, beam_width: int
                               ) -> list[tuple[str, str]]:
        """κ_required = κ_M1 + κ_M2: gerekli imzayı iki moleküle böl."""
        from tantrium.core.quantum_moments import FreeCumulants
        krq = FreeCumulants.from_moments(mu_req)
        # Her yarı ≈ krq/2 (yaklaşık)
        k_half = FreeCumulants([x / 2.0 for x in krq.k])
        mu_half = k_half.to_moments_approx()
        if mu_half and mu_half[0] > 0:
            try:
                from tantrium.core.molecular_derivation import MolecularGenesis
                rep1 = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES[:3], max_steps=max(4, max_steps // 2),
                    beam_width=max(2, beam_width // 2), toward_profile=[mu_half])
                rep2 = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES[3:], max_steps=max(4, max_steps // 2),
                    beam_width=max(2, beam_width // 2), toward_profile=[mu_half])
                pairs = []
                front1 = [s.smiles for s in rep1.frontier if self._chemically_stable(s.smiles)]
                front2 = [s.smiles for s in rep2.frontier if self._chemically_stable(s.smiles)]
                for s1 in front1[:3]:
                    for s2 in front2[:3]:
                        if s1 != s2:
                            pairs.append((s1, s2))
                return pairs[:6]
            except Exception:
                pass
        return []

    def _inject_manifold(self, smiles: str, concept_name: str) -> str:
        """Kabul edilen molekülü manifolda kavram olarak ekle (idempotent)."""
        label = f"drug:{concept_name[:20]}:{smiles[:12]}"
        if label in self.engine.manifold.concepts:
            return label  # idempotent
        try:
            mu = self._encode(smiles)
            if not mu:
                return ""
            from tantrium.core.concept import Concept
            c = Concept(name=label, moments=mu, domain="drug", source="produce")
            self.engine.manifold.add(c)
            return label
        except Exception:
            return ""
