"""Tantrium AI — taban sınıf: kurulum (engine) + paylaşılan private yardımcılar.

Mixin'lerin ortak kullandığı durumsuz yardımcılar burada toplanır. AI() davranışı
değişmez; bu sınıf yalnız MRO tabanı ve paylaşılan iç araçları sağlar.
"""
from __future__ import annotations


class _AIBase:
    """Tantrium — taban: engine kurulumu + paylaşılan yardımcılar.

    Mixin'ler bu sınıfın `self._engine`'ini ve private metotlarını kullanır.
    """

    def __init__(self, persist: bool = True) -> None:
        """
        persist=True: manifold her işlemden sonra otomatik kaydedilir.
        """
        from tantrium.core.engine import CertificationEngine
        self._engine = CertificationEngine()
        self._persist = persist
        self._mol_gen = None   # lazy init
        self._certifier = None # lazy init

    @property
    def engine(self):
        """Ham AGIEngine — gelişmiş kullanım için."""
        return self._engine

    # ── Lazy helpers ─────────────────────────────────────────────────────────

    def _get_certifier(self):
        if self._certifier is None:
            from tantrium.domains.certifier import MolecularCertifier
            self._certifier = MolecularCertifier(self._engine)
        return self._certifier

    def _get_mol_gen(self):
        if self._mol_gen is None:
            from tantrium.domains.generator import MoleculeGenerator
            self._mol_gen = MoleculeGenerator(self._engine)
        return self._mol_gen

    def _pe(self):
        """Lazy ProductionEngine (Sturm-yol sertifikası için paylaşılır)."""
        pe = getattr(self, "_pe_cache", None)
        if pe is None:
            from tantrium.core.production import ProductionEngine
            pe = ProductionEngine(self._engine)
            self._pe_cache = pe
        return pe

    def _concept_moments(self, name: str) -> list:
        c = self._engine.manifold.concepts.get(name)
        if c is not None:
            return [float(m) for m in c.moments]
        try:
            return [float(m) for m in self._engine.encoder.encode(name).moments]
        except Exception:
            return []

    def _sturm_chain_ok(self, path: list) -> tuple:
        """RH-LİTERAL: çıkarım yörüngesi gerçek-ölçü manifoldunda mı (Sturm pivot ≥ 0 =
        hiperbolik = kritik hat üzerinde). İlaç-gerçeklenebilirliğiyle AYNI sertifika."""
        pe = self._pe()
        mins = []
        for i in range(0, len(path) - 2, 2):
            ma, mb = self._concept_moments(path[i]), self._concept_moments(path[i + 2])
            if ma and mb:
                try:
                    _ok, pmin = pe._sturm_path_pivot_min(ma, mb)
                    mins.append(float(pmin))
                except Exception:
                    pass
        return (min(mins) >= -1e-3 if mins else True), (min(mins) if mins else 0.0)

    @staticmethod
    def _extract_numbers(text: str) -> list:
        """İstekten sayı dizisini çıkar (virgül/boşluk ayrık, ondalık/negatif dahil)."""
        import re
        return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(text))]

    _AA20 = "ACDEFGHIKLMNPQRSTVWY"   # 20 standart amino asit (tek harf)

    def _target_moments_for_peptide(self, target) -> list:
        """Hedef (peptit dizisi / liste / protein adı / SMILES) → hedef moment imzası.
        Genel evrensel encoder (spektral moment) — dizi ya da metin fark etmez."""
        if isinstance(target, (list, tuple)):
            return [float(m) for m in target]
        s = str(target).strip()
        return [float(m) for m in self._engine.encoder.encode(s).moments]

    def _parse_numeric_series(self, source) -> list:
        """Yapısal kaynaktan (liste/JSON/CSV/metin) sayı dizisini DETERMİNİSTİK çıkar."""
        if isinstance(source, (list, tuple)):
            out = []
            for x in source:
                try:
                    out.append(float(x))
                except (TypeError, ValueError):
                    pass
            return out
        s = str(source).strip()
        # JSON listesi dene
        try:
            import json as _json
            v = _json.loads(s)
            if isinstance(v, list):
                return self._parse_numeric_series(v)
            if isinstance(v, dict):
                return self._parse_numeric_series(list(v.values()))
        except Exception:
            pass
        # CSV/TSV: her satırın SON sayısal alanı (zaman serisi sütunu)
        lines = [ln for ln in s.splitlines() if ln.strip()]
        if len(lines) >= 3 and any(("," in ln or "\t" in ln) for ln in lines):
            col = []
            for ln in lines:
                nums = self._extract_numbers(ln)
                if nums:
                    col.append(nums[-1])
            if len(col) >= 3:
                return col
        # düz metin: tüm sayılar
        return self._extract_numbers(s)

    def _ext_moments(self, query):
        """16-derinlik genişletilmiş moment (encoder._extract_structure ile aynı mantık)."""
        from tantrium.core.encoder import _spectral_moments, _try_power_moments
        ext = _try_power_moments(query, 16)
        if ext is None:
            ext = _spectral_moments(self._engine.encoder._to_matrix(query), 16)
        return ext

    # ── Protein → referans ligand (üretim/yargı mixin'leri paylaşır) ─────────

    # Statik protein→bilinen-inhibitör haritası (TAU eksikse geri düşme)
    _PROTEIN_DIRECT_MAP: dict[str, list[str]] = {
        "egfr":   ["erlotinib", "gefitinib", "afatinib", "osimertinib"],
        "her2":   ["lapatinib", "afatinib"],
        "braf":   ["vemurafenib", "sorafenib"],
        "kit":    ["imatinib", "sunitinib"],
        "src":    ["dasatinib", "bosutinib", "imatinib"],
        "abl":    ["imatinib", "dasatinib", "bosutinib"],
        "akt":    ["ipatasertib", "capivasertib"],
        "akt1":   ["ipatasertib", "capivasertib"],
        "mek":    ["trametinib", "cobimetinib"],
        "mek1":   ["trametinib", "cobimetinib"],
        "jak":    ["ruxolitinib", "tofacitinib", "baricitinib"],
        "jak2":   ["ruxolitinib", "tofacitinib", "baricitinib"],
        "jak1":   ["tofacitinib", "baricitinib"],
        "parp":   ["olaparib", "niraparib", "rucaparib"],
        "parp1":  ["olaparib", "niraparib", "rucaparib"],
        "cdk4":   ["palbociclib", "ribociclib", "abemaciclib"],
        "cdk6":   ["palbociclib", "ribociclib", "abemaciclib"],
        "alk":    ["alectinib", "brigatinib", "crizotinib"],
        "mtor":   ["everolimus", "temsirolimus"],
        "vegfr":  ["sorafenib", "sunitinib", "vandetanib"],
        "vegfr2": ["sorafenib", "sunitinib", "vandetanib"],
        "stat3":  ["sorafenib", "sunitinib"],
        "btk":    ["ibrutinib"],
        "pdgfr":  ["imatinib", "sorafenib", "sunitinib"],
        "ret":    ["vandetanib", "cabozantinib"],
    }

    def _protein_reference_ligands(self, protein: str, top_refs: int = 8
                                   ) -> list[tuple[str, str]]:
        """Proteinin bilinen ligandlarını gerçek SMILES'a çözümle.

        Protein word-encode EDİLMEZ. TAU'daki INHIBITS/ACTIVATES kenarları →
        ligand isimleri → ilaç kütüphanesinden SMILES. Hiçbiri çözülemezse
        _PROTEIN_DIRECT_MAP statik haritasına, oradan da terapötik sınıfa düşer.
        Boş liste = referans yok (dürüst).
        """
        from tantrium.core.molecular_space import DRUG_LIBRARY
        name2smi = {n.lower(): smi for n, smi, _ in DRUG_LIBRARY}
        name2cls = {n.lower(): cls for n, _, cls in DRUG_LIBRARY}
        prot = protein.lower().strip()
        tau = self.engine.tau

        ligand_names: list[str] = []
        for _src, elist in tau.edges.items():
            for e in elist:
                tgt = str(getattr(e, "target", "")).lower()
                par = getattr(e, "paradigm", "")
                if tgt == prot and par in ("INHIBITS", "ACTIVATES", "TARGETS", "BINDS"):
                    ligand_names.append(str(_src).lower())

        ref: list[tuple[str, str]] = []
        ref_cls = None
        for nm in dict.fromkeys(ligand_names):
            if nm in name2smi:
                ref.append((nm, name2smi[nm]))
                ref_cls = ref_cls or name2cls.get(nm)

        # Statik harita ile tamamla (TAU eksik veya yetersiz olduğunda)
        seen = {n for n, _ in ref}
        if prot in self._PROTEIN_DIRECT_MAP:
            for nm in self._PROTEIN_DIRECT_MAP[prot]:
                if nm not in seen and nm in name2smi:
                    ref.append((nm, name2smi[nm]))
                    ref_cls = ref_cls or name2cls.get(nm)
                    seen.add(nm)

        if not ref and ref_cls:
            ref = [(n.lower(), s) for n, s, c in DRUG_LIBRARY if c == ref_cls][:top_refs]
        return ref[:top_refs]

    def _canonical_kappa(self):
        """Sağlıklı/dengeli referans κ — sistemin kanonik ζ ailesi.

        Her şey ζ-sıfırlarına göre ölçülür; 'denge' = kanonik spektral aile.
        Bulunamazsa serbest-Gauss (yarı-daire, κ_k=0 k≥3) referansına düşer.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                return FreeCumulants.from_moments([float(m) for m in c.moments])
        return FreeCumulants([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
