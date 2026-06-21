"""Yardımcı mixin — imza/encode, kimya, referans-ligand, eşik, flywheel kancaları.

_signature / _encode / _is_smiles / _chemically_stable / _n_atoms /
_reference_ligands / _disease_drivers / _kappa_threshold /
_sync_transport_epsilon / scan_production_gaps / _canonical_kappa.
"""
from __future__ import annotations

from ._types import (
    _DISEASE_DRIVER_MAP,
    _PROTEIN_DIRECT_MAP,
    MoleculeSignature,
)


class _HelpersMixin:
    # ── Yardımcılar ────────────────────────────────────────────────────────

    def _signature(self, x: str) -> "MoleculeSignature":
        """Molekülün TEK imzası — bir kez encode, cache. Pipeline'ın taşıdığı nesne.

        Tüm üretim aşamaları (ranking·judge·closure) bunu çağırır → molekül bir kez
        encode edilir; κ/özdeğer imzadan lazy gelir. Yeniden-encode dağınıklığı biter.
        """
        sig = self._sig_cache.get(x)
        if sig is None:
            mu: list[float] = []
            struct = None
            try:
                obj = self.engine.encoder.encode(x)
                mu = [float(m) for m in obj.moments]
                struct = getattr(obj, "structure", None)
            except Exception:
                mu = []
            sig = MoleculeSignature(smiles=x, mu=mu, structure=struct)
            self._sig_cache[x] = sig
        return sig

    def _encode(self, x: str) -> list[float]:
        """İmzanın momentleri (geriye-uyum). TEK imza cache'ine delege — re-encode yok."""
        return self._signature(x).mu

    @staticmethod
    def _is_smiles(s: str) -> bool:
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(s)
            return (mol is not None and any(c in s for c in "()=#[]12")
                    or (len(s) >= 2
                        and all(c in "CNOSPFclnosbr()=#[]+-1234567890@/\\H" for c in s)
                        and " " not in s))
        except Exception:
            return (" " not in s and len(s) >= 2 and any(c in s for c in "()=#[]12"))

    @staticmethod
    def _chemically_stable(smiles: str) -> bool:
        """GIMEL Aşil topuğu: zayıf bağ motifleri eler (peroksit, triokso...)."""
        s = smiles.upper()
        for bad in ("OO", "OOO", "NNN", "SSS", "FF", "NOO", "OON"):
            if bad in s:
                return False
        return True

    def _n_atoms(self, smiles: str) -> int:
        try:
            from rdkit import Chem
            m = Chem.MolFromSmiles(smiles)
            return m.GetNumAtoms() if m else 0
        except Exception:
            return sum(1 for c in smiles if c.isalpha())

    def _reference_ligands(self, protein: str, top_refs: int = 8
                           ) -> list[tuple[str, str]]:
        """Proteinin bilinen ligandları → SMILES (word-encode YOK)."""
        try:
            from tantrium.core.molecular_space import DRUG_LIBRARY
        except Exception:
            return []
        name2smi = {n.lower(): smi for n, smi, _ in DRUG_LIBRARY}
        name2cls = {n.lower(): cls for n, _, cls in DRUG_LIBRARY}
        prot = protein.lower().strip()
        tau = getattr(self.engine, "tau", None)
        if tau is None:
            return []
        names: list[str] = []
        for _src, elist in tau.edges.items():
            for e in elist:
                tgt = str(getattr(e, "target", "")).lower()
                par = getattr(e, "paradigm", "")
                if tgt == prot and par in ("INHIBITS", "ACTIVATES", "TARGETS", "BINDS"):
                    names.append(str(_src).lower())
        ref: list[tuple[str, str]] = []
        ref_cls = None
        for nm in dict.fromkeys(names):
            if nm in name2smi:
                ref.append((nm, name2smi[nm]))
                ref_cls = ref_cls or name2cls.get(nm)
        # Statik harita ile tamamla (TAU eksik veya yetersiz olduğunda)
        seen = {nm for nm, _ in ref}
        if prot in _PROTEIN_DIRECT_MAP:
            for nm in _PROTEIN_DIRECT_MAP[prot]:
                if nm not in seen and nm in name2smi:
                    ref.append((nm, name2smi[nm]))
                    ref_cls = ref_cls or name2cls.get(nm)
                    seen.add(nm)
        if not ref and ref_cls:
            ref = [(n.lower(), s) for n, s, c in DRUG_LIBRARY if c == ref_cls][:top_refs]
        return ref[:top_refs]

    def _disease_drivers(self, disease: str) -> list[str]:
        """Hastalığın DRUGGABLE moleküler sürücüleri — statik harita + TAU disease→sürücü.

        Hastalığı METİN olarak değil, onu süren GERÇEK druggable hedeflerden ölç.
        Yalnız ligandı olan (kürede _PROTEIN_DIRECT_MAP'te) sürücüleri alır → ölçülebilir.
        """
        d = disease.lower().strip()
        drivers: list[str] = [p for p in _DISEASE_DRIVER_MAP.get(d, [])]
        tau = getattr(self.engine, "tau", None)
        if tau is not None:
            for e in tau.edges.get(d, []):
                par = getattr(e, "paradigm", "")
                if par in ("CAUSES", "ACTIVATES", "INHIBITS", "COMPONENT_OF", "IS_A"):
                    t = str(getattr(e, "target", "")).lower()
                    # yalnız druggable (ligandı olan) sürücüleri ölç
                    if t and t in _PROTEIN_DIRECT_MAP and t not in drivers:
                        drivers.append(t)
        return drivers

    def _kappa_threshold(self, profiles: list[list[float]]) -> float:
        """Özgüllük eşiği — referans sınıf-içi genişliğinden."""
        valid = [p for p in profiles if p]
        if not valid:
            return float("inf")
        if len(valid) == 1:
            return 0.5
        dists = [self._structural_kappa_distance(valid[i], valid[j])
                 for i in range(len(valid)) for j in range(i + 1, len(valid))]
        avg = sum(dists) / len(dists) if dists else 0.0
        return avg + 0.25

    # ── Dökümhane ↔ İspat Flywheel ───────────────────────────────────────────

    def _sync_transport_epsilon(self) -> None:
        """Theorem graph'taki Sturm sertifikasını oku → transport eşiğini genişlet.

        subresultant_recurrence kampanyası qjr_degree_j_shift + qjr_degree_r_step'i
        kanıtlarsa: pivot eşiği -1e-9 → -1e-5. Daha geniş koridor = daha fazla geçen
        molekül. Flywheel: ispat → genişleme → üretim kalitesi artar → yeni boşluk.
        """
        try:
            import json
            from pathlib import Path
            _INJECTED_STATUSES = {"PROVEN_BY_CERTIFICATE",
                                  "RECURRENCE_VERIFIED_FINITE", "CERTIFIED_LOCAL"}
            graph_path = (Path(__file__).resolve().parents[4]
                          / "tantrium" / "theorem_graph" / "theorem_graph.yaml")
            if not graph_path.exists():
                return
            with open(graph_path) as f:
                data = json.load(f)
            nodes = data.get("nodes", {})
            sturm_nodes = ["qjr_degree_j_shift", "qjr_degree_r_step"]
            if all(nodes.get(n, {}).get("status") in _INJECTED_STATUSES
                   for n in sturm_nodes):
                self._transport_epsilon = -1e-5
        except Exception:
            pass

    def scan_production_gaps(self, cert: "ProductionCertificate") -> list[str]:
        """Başarısız sertifika eksenlerini ProofLoop kampanya ipuçlarına çevir.

        Dökümhane↔İspat flywheel'inin giriş noktası:
          transport başarısız → "transport" → subresultant_recurrence kampanyası
          quantum başarısız   → "quantum"   → rh_formalization kampanyası
          closure başarısız   → "closure"   → lah_gate_ab kampanyası

        Kullanım:
          gaps = pe.scan_production_gaps(cert)
          if "transport" in gaps:
              ProofLoop(engine).launch_campaign("subresultant_recurrence")
        """
        gaps: list[str] = []
        for ax in (cert.axes or []):
            if not ax.ok and ax.name not in gaps:
                gaps.append(ax.name)
        if cert.closure and not cert.closure.universe_closes and "closure" not in gaps:
            gaps.append("closure")
        if cert.verdict in ("ÜRETİLEMEDİ", "KISMÎ") and not gaps:
            gaps.append("generic")
        return gaps

    def _canonical_kappa(self):
        """Sağlıklı denge κ — kanonik ζ ailesi (RH çapası)."""
        from tantrium.core.quantum_moments import FreeCumulants
        for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                return FreeCumulants.from_moments([float(m) for m in c.moments])
        return FreeCumulants([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
