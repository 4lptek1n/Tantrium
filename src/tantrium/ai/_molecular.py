"""Tantrium AI — moleküler / üretim yüzeyi (MolecularMixin).

transport / discover / design / arrange / morph / lineage_mol / genesis_mol /
design_drug / cure / simulate / produce / produce_math / cross / judge_binding /
design_peptide.
"""
from __future__ import annotations

from ._results import MolResult, DiscoverResult, DesignResult


class MolecularMixin:
    """De novo molekül üretimi, ters transport, üretim dökümhanesi metotları."""

    def transport(self, source: str, target: str, use_smiles: bool = False) -> "object":
        """Certified dyadic transport from source → target moment sequences.

        Three-layer proof:
          1. Dyadic: exact rational mass coverage (solve_greedy → verified_exact)
          2. Sturm: H(t)=(1-t)H_src + t*H_tgt stays PSD throughout (real measure manifold)
          3. Zeta: distance from target spectral family to Riemann ζ-zeros family

        Better than nearest-neighbor: paths through non-PSD territory (STURM_FAILED)
        are rejected even if closer in moment distance.

        use_smiles=True: encode source/target as molecular SMILES (Morgan ECFP4)
        use_smiles=False: encode as general text/semantic input (bigram matrix)

        Döner: TransportCertificate(certified, dyadic_verified, sturm_verified, zeta_distance, ...)
        """
        from tantrium.core.transport import CertifiedTransport

        def _looks_like_smiles(s: str) -> bool:
            """Heuristic SMILES detection."""
            smiles_chars = set("CNOSPFClBrI[]()=#@/\\+1234567890-")
            return len(s) >= 3 and len(s) <= 200 and all(c in smiles_chars for c in s)

        if use_smiles or (_looks_like_smiles(source) and _looks_like_smiles(target)):
            from tantrium.core.encoder import encode_smiles
            src_obj = encode_smiles(source, name=source[:64])
            tgt_obj = encode_smiles(target, name=target[:64])
        else:
            from tantrium.core.encoder import encode as _enc
            src_obj = _enc(source, name=source[:64])
            tgt_obj = _enc(target, name=target[:64])

        ct = CertifiedTransport(self._engine)
        # Pass full CodexObjects so transport uses eigenvalue spectrum (pipeline output)
        return ct.certify(src_obj, tgt_obj)

    def discover(
        self,
        target: str,
        top_k: int = 8,
        out_dir: str = "results/molecules",
    ) -> DiscoverResult:
        """Hedef → Morgan moment uzayı → de novo molekül üretimi → 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.domains.generator import MoleculeGenerator

        gen = self._get_mol_gen()
        report = gen.generate(target, top_k=top_k, out_dir=out_dir)

        candidates = [
            MolResult(
                name=c.name,
                smiles=c.smiles,
                certified=c.certified_count > 0,
                paradigms_passed=c.certified_count,
                paradigms_total=c.total_paradigms,
                dyadic_score=c.dyadic_score,
                sdf=c.sdf_path,
                gaps=[],
            )
            for c in report.candidates
        ]
        best = None
        if report.best:
            best = next((c for c in candidates if c.name == report.best.name), None)

        return DiscoverResult(
            target=target,
            candidates=candidates,
            best=best,
            duration_s=report.duration_s,
        )

    def design(
        self,
        target: str,
        top_k: int = 10,
        out_dir: str = "results/molecules",
        n_fragment_rounds: int = 2,
    ) -> "DesignResult":
        """Ters transport — hedef → W2-minimal moleküller → 3D SDF.

        Manifold araması (L1→W2) + fragment mutasyonu + 4-eksen sertifika.
        target: protein adı, hastalık işareti, SMILES veya herhangi metin.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.inverse import InverseTransport
        inv = InverseTransport(self.engine)
        report = inv.design(target, top_k=top_k, out_dir=out_dir,
                            n_fragment_rounds=n_fragment_rounds)
        return DesignResult(
            target=report.target,
            target_type=report.target_type,
            candidates=report.candidates,
            best=report.best,
            duration_s=report.duration_s,
            n_manifold=report.n_manifold,
            n_fragment=report.n_fragment,
        )

    def arrange(
        self,
        target: str,
        n: int = 12,
        cls_filter: str | None = None,
    ) -> "object":
        """Moleküler düzenleme — hedef etrafında W2 mesafesine göre 150+ ilaç diz.

        Saf matematiksel. Metin arama yok — her molekül G=AᵀA → μ_k kernel'den geçer.
        target: protein, hastalık, SMILES veya herhangi bir kavram.
        cls_filter: "kinase", "nsaid", "oncology", "natural", vb.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.arrange(target, n=n, cls_filter=cls_filter)

    def morph(
        self,
        source_smiles: str,
        target_smiles: str,
        steps: int = 6,
    ) -> "object":
        """İki molekül arasında moment uzayında interpolasyon yolu.

        Her ara noktada kütüphaneden en yakın gerçek molekül bulunur.
        A → B arasındaki kimyasal evrim yolunu gösterir.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.morph(source_smiles, target_smiles, steps=steps)

    def lineage_mol(
        self,
        smiles: str,
        depth: int = 3,
    ) -> list:
        """Moleküler silsile — W2 ağacında ata-torun zinciri.

        Her seviyede 3 en yakın kimyasal akraba. Molekülün 'kimden geldiğini' gösterir.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.lineage(smiles, depth=depth)

    def genesis_mol(
        self,
        target: str,
        top_k: int = 6,
        max_atoms: int = 16,
        beam_width: int = 4,
    ) -> "object":
        """Moleküler Genesis — saf matematiksel türetim. Tahmin yok.

        Hedef → momentler → Gauss-Bolyai spektral ölçü → yapı kılavuzu
        → atom-atom beam search (W2 azaldıkça ilerle) → sertifika.

        Benzerlik araması değil: matematiksel zorunluluktan türev.
        target: protein, hastalık, SMILES, herhangi metin.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_derivation import MolecularGenesis
        gen = MolecularGenesis(self.engine)
        return gen.generate(target, top_k=top_k, max_atoms=max_atoms, beam_width=beam_width)

    # ── Evren simülasyonu: makineyi çalıştırarak ilaç üret ───────────────────

    def design_drug(self, protein: str, max_steps: int = 16, beam_width: int = 6,
                    out_dir: str = "results/molecules") -> dict:
        """Protein → kanıtlı ilaç adayları + 3D SDF. produce() üzerinden çalışır."""
        refs = self._protein_reference_ligands(protein)
        if not refs:
            return {"protein": protein, "verdict": "BİLİNMİYOR",
                    "reason": f"'{protein}' için referans ligand yok — yön kurulamıyor.",
                    "candidates": []}
        from tantrium.core.production import ProductionEngine
        cert = ProductionEngine(self.engine).produce(
            protein, max_steps=max_steps, beam_width=beam_width,
            out_dir=out_dir, inject=False)
        result = cert.to_design_dict()
        result["n_refs"] = len(refs)
        result["reference_ligands"] = [n for n, _ in refs]
        return result

    def cure(self, disease: str, max_steps: int = 14, beam_width: int = 5,
             out_dir: str = "results/molecules") -> dict:
        """Hastalık → κ-dekonvolüsyon → kanıtlı molekül + 3D SDF. produce() üzerinden."""
        from tantrium.core.production import ProductionEngine
        cert = ProductionEngine(self.engine).produce(
            disease, max_steps=max_steps, beam_width=beam_width,
            out_dir=out_dir, inject=False)
        return cert.to_cure_dict()

    def simulate(self, seed: str = "CC", max_steps: int = 14,
                 beam_width: int = 5, toward: str | None = None) -> "object":
        """Evren simülasyonu — makineyi çalıştırarak molekülü transport ile diz.

        Hafızadan benzer arama YOK. Her atom-ekleme adımı CertifiedTransport ile
        yargılanır: sturm-PSD (gerçek-ölçü geçidi) + dyadic (sertifika bonusu) +
        zeta (Riemann ζ derinliği = sürekli yön). Makinenin kendisi molekülü
        sıfırdan inşa eder, sonsuza dek ilerletir.

        seed: başlangıç SMILES   toward: opsiyonel yön (gradyan, eşleşme değil)
        """
        from tantrium.core.molecular_derivation import MolecularGenesis
        return MolecularGenesis(self.engine).simulate(
            seed=seed, max_steps=max_steps, beam_width=beam_width, toward=toward)

    def produce(self, target: "str | list[float]", max_steps: int = 16, beam_width: int = 6,
                out_dir: str = "results/molecules", refine_rounds: int = 2,
                combination: bool = True, network: bool = False, inject: bool = True,
                epsilon: float = 0.5, top_k: int = 10) -> "object":
        """TEK GİRİŞ — çok-stratejili üret → evren-kapat → 6-eksen sertifikala.

        target: kavram/hastalık/SMILES string VEYA moment listesi
        ai.produce("egfr")                          # protein → bilinen ligand profili
        ai.produce("c1ccc2ncnc(N)c2c1")            # SMILES → doğrudan imza
        ai.produce("alzheimer")                     # hastalık → ters dekonvolüsyon
        ai.produce(ai.meaning_compose("...").to_produce_target())  # komposisyonel

        NOT: 3D docking, ADMET, off-target yok. Spektral zorunluluk (gerekli
        koşul); biyolojik geçerlilik wet-lab ile.
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).produce(
            target, max_steps=max_steps, beam_width=beam_width, out_dir=out_dir,
            refine_rounds=refine_rounds, combination=combination, network=network,
            inject=inject, epsilon=epsilon, top_k=top_k)

    def produce_math(self, disease, build: bool = False, healthy=None) -> "object":
        """Hastalık → ilaç, TAMAMEN MATEMATİK (harf/SMILES yok) — RH parçaları zinciri.

        disease:
          • moment listesi (sayılar) — ÖLÇÜLEN hastalık imzası (lab spektrumu). En dürüst:
            hastalık bir küme sayı, isim değil.
          • bulgu listesi (str) — ölçülen sinyaller; κ'ya çekilip serbest-toplanır.

        Akış (her adım RH parçası, hepsi sayı): κ_disease → κ_healthy ⊟ κ_disease = κ_drug
        → μ_drug → özdeğer ölçüsü (İLACIN KENDİSİ) → Hankel-PSD (D-poz) ∧ Sturm pivot
        (Jensen) = gerçeklenebilirlik (RH sertifikası).

        build=True: SON ADIM — düzeltici spektruma en yakın gerçeklenebilir YAPIYI (molekül)
          kurar. Ölçülen hastalık (sayı) → gerçek ilaç (yapı) baştan sona TEK akış; harf
          yalnız en sonda. .designed_smiles / .n_atoms doldurulur.
        Döner: MathDrug (.summary() insan-okunur; .eigenvalues = ilacın spektrumu).
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).produce_math(disease, build=build, healthy=healthy)

    def cross(self, disease, drug: str, dna: str) -> "object":
        """ÜÇLÜ CROSS — sanal wet-lab: hastalık × ilaç × KİŞİNİN DNA'sı → işe yarar mı.

        disease: ölçülen hastalık (sayı/bulgu/isim) → κ_disease
        drug   : ilaç (SMILES) → κ_drug
        dna    : kişinin DNA dizisi (ATCG...) → κ_dna  (kişinin sağlıklı tabanı)

        İki eksen (κ-uzayı, kişiye özel):
          ETKİLİLİK: κ(hastalık ⊞ ilaç) kişinin DNA tabanına dönüyor mu (Sturm + κ-hata).
          UYUMLULUK: κ(ilaç ⊞ DNA) gerçeklenebilir mi (Hankel-PSD + pürüzsüz yol = advers yok).
        Aynı hastalık+ilaç, FARKLI DNA → farklı yargı. Wet-lab'in eleme işini matematik yapar.
        Döner: CrossResult (.summary() insan-okunur; .works/.verdict).
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).cross_check(disease, drug, dna)

    # Paradigma-matematik mesafe eşiği (45-özellik normalize imza):
    # EGFR-içi ≤3.43, kinaz-sınıfı ≤4.18, kinaz-dışı ≥4.25 → 4.5 = sınıf ayracı.
    # judge_binding "aynı terapötik sınıf mı?" sorar — üretimden daha geniş.
    _PARADIGM_WORKS_THR = 4.5

    def judge_binding(self, candidate: str, protein: str, top_refs: int = 8) -> dict:
        """İşe yarar mı? — adayı proteinin bilinen ligandlarına karşı
        PARADİGMA-MATEMATİK mesafesi ile yargıla.

        Sertifika 'geçti/✓' SAYMAZ — paradigmaların hesapladığı SAYILARI kullanır:
        özdeğer spektrumu (DALET), Lyapunov (HE), Li katsayıları (HET), de
        Bruijn-Newman Λ (TAV), alt-resultant, Schur, spektral entropi → ölçek-
        bağımsız imza. Aday bu imzada bilinen bir ligandla 'aynı tür' çıkarsa
        (mesafe < eşik) işe yarar. κ-kuantum mesafesi ikincil sinyal.

        Protein word-encode EDİLMEZ — ligandları gerçek SMILES'a çözümlenir.
        candidate: SMILES   protein: hedef adı (egfr, bcr-abl, ...)
        """
        from tantrium.core.quantum_moments import QuantumSignature
        from tantrium.core.metric import paradigm_distance

        ref_smiles = self._protein_reference_ligands(protein, top_refs)
        if not ref_smiles:
            return {
                "candidate": candidate, "protein": protein,
                "verdict": "BİLİNMİYOR",
                "reason": f"'{protein}' için SMILES'a çözümlenebilen bilinen ligand yok — "
                          f"yargılamak için referans gerekiyor.",
                "n_refs": 0,
            }

        # Aday: paradigma matematik imzası + κ imzası (moleküler encode — kelime değil)
        try:
            cand_obj = self.engine.encoder.encode(candidate)
            cand_struct = cand_obj.structure
            cand_sig = QuantumSignature.from_moments([float(m) for m in cand_obj.moments])
        except Exception:
            return {"candidate": candidate, "protein": protein,
                    "verdict": "GEÇERSİZ", "reason": "Aday encode edilemedi.", "n_refs": 0}

        # Her referans ligandla paradigma-matematik + κ mesafesi
        best = None  # (name, paradigm_dist, kappa_dist)
        for nm, smi in ref_smiles[:top_refs]:
            try:
                ref_obj = self.engine.encoder.encode(smi)
                pd = paradigm_distance(cand_struct, ref_obj.structure)
                ref_sig = QuantumSignature.from_moments(
                    [float(m) for m in ref_obj.moments])
                kd = cand_sig.cumulants.distance(ref_sig.cumulants)
            except Exception:
                continue
            if best is None or pd < best[1]:
                best = (nm, pd, kd)

        if best is None:
            return {"candidate": candidate, "protein": protein, "verdict": "GEÇERSİZ",
                    "reason": "Referans imzaları hesaplanamadı.", "n_refs": len(ref_smiles)}

        nearest_name, nearest_pd, nearest_kd = best
        gc = self.grounding(candidate)

        # YARGI: paradigmaların kendi matematiğinde 'aynı tür' mü?
        works = nearest_pd < self._PARADIGM_WORKS_THR
        verdict = "İŞE YARAYABİLİR" if works else "İŞE YARAMAZ"

        return {
            "candidate": candidate, "protein": protein, "verdict": verdict,
            "n_refs": len(ref_smiles),
            "nearest_ligand": nearest_name,
            "paradigm_dist_to_nearest": round(nearest_pd, 4),
            "kappa_dist_to_nearest": round(nearest_kd, 4),
            "grounding": gc.verdict,
            "reason": (f"En yakın bilinen ligand '{nearest_name}': paradigma-matematik "
                       f"mesafesi {nearest_pd:.3f} (eşik {self._PARADIGM_WORKS_THR}); "
                       f"κ={nearest_kd:.3f}. "
                       f"{'Aynı yapısal tür.' if works else 'Farklı tür.'}"),
        }

    def design_peptide(self, target, *, max_residues: int = 8, beam_width: int = 3,
                       seed: str = "G") -> dict:
        """ASI Pilar C — DETERMİNİSTİK BİYOPOLİMER (peptit) TASARIMI, kalıntı-kalıntı Sturm-certified.

        molecular_derivation'in atom-atom Sturm-certified büyümesini AMİNO ASİDE taşır: her AA ekleme
        `CertifiedTransport.certify(fast_sturm=True)` ile sertifikalı (Sturm SERT geçit = gerçek-ölçü
        yolu); skor hedef-spektruma (`encode_protein` Kyte-Doolittle moment) yakınlık. Deterministik
        beam (random YOK) → aynı hedef birebir aynı peptit.

        DÜRÜST SINIR (kullanıcı kararı): 3D fold (AlphaFold/istatistik) YOK — köklü DİZİ (FASTA) +
        spektral/Sturm sertifikası. "Bizde istatistik deterministiktir" — fold tahmini değil, dizi-
        seviye deterministik tasarım. FARK: her kalıntı Sturm-certified, tekrar üretilebilir.
        Döner: {target, peptide, n_residues, sturm_steps_ok, fit, answer}.
        """
        from tantrium.core.transport import CertifiedTransport
        tmu = self._target_moments_for_peptide(target)
        ct = CertifiedTransport(self._engine)
        _enc_cache: dict = {}

        def _enc(seq):
            o = _enc_cache.get(seq)
            if o is None:
                o = self._engine.encoder.encode(seq); _enc_cache[seq] = o
            return o

        def _dist(seq) -> float:
            mu = [float(m) for m in _enc(seq).moments]
            k = min(len(mu), len(tmu))
            return sum(abs(mu[i] - tmu[i]) for i in range(k))

        beam = [seed]
        steps_ok = 0
        for _ in range(max(0, max_residues - len(seed))):
            cands: list = []
            for base in beam:
                base_obj = _enc(base)
                for aa in self._AA20:        # deterministik sıra (random yok)
                    ext = base + aa
                    try:
                        tc = ct.certify(base_obj, _enc(ext), fast_sturm=True)
                        if not getattr(tc, "sturm_verified", False):
                            continue          # Sturm SERT geçit: gerçek-ölçü yolu değilse ele
                        cands.append((ext, _dist(ext)))
                    except Exception:
                        continue
            if not cands:
                break
            cands.sort(key=lambda x: (x[1], x[0]))   # mesafe, sonra deterministik tie-break
            beam = [c[0] for c in cands[:beam_width]]
            steps_ok += 1
        best = min(beam, key=lambda s: (_dist(s), s)) if beam else seed
        fit = round(_dist(best), 5)
        ans = (f"'{target}' hedefine deterministik peptit tasarladım: {best} "
               f"({len(best)} kalıntı). Her kalıntı ekleme Sturm-certified (kritik hat) — "
               f"spektral uyum {fit}. 3D fold YOK (istatistik): köklü DİZİ + sertifika, "
               f"tekrar üretilebilir. Mythos istatistikle üretir; ben her adımı sertifikalarım."
               if steps_ok else
               f"'{target}' için Sturm-certified peptit yolu kuramadım (kısıt sıkı).")
        return {"target": str(target), "peptide": best, "n_residues": len(best),
                "sturm_steps_ok": steps_ok, "fit": fit, "answer": ans}
