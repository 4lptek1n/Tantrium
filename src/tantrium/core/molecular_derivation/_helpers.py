"""Moleküler Genesis — kodlama / spektral kılavuz / beam-inşa yardımcıları.

MolecularGenesis'in hedef-kodlama, spektral okuma, kuantum skor ve atom-atom
beam-büyütme metotlarını içeren mixin. Çekirdek (generate/simulate) _genesis.py'de.
"""
from __future__ import annotations

from ._types import GenesisCandidate


class _GenesisHelpers:
    """MolecularGenesis için kodlama + spektral kılavuz + beam-inşa metotları.

    Bu sınıf bir mixin'dir: ``self.engine`` MolecularGenesis tarafından sağlanır.
    """

    # ── Hedef kodlama ────────────────────────────────────────────────────────

    def _encode_target(self, target: str) -> tuple[list[float], str]:
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

    @staticmethod
    def _mol_spec(smiles: str):
        """Moleküler Laplacian eigenvalue'larından SpectralMeasure.

        encode_smiles() kullanarak string-gram değil, gerçek moleküler
        spektrum alıyoruz — C, CC, CCC artık ayırt edilebilir.
        """
        try:
            from tantrium.core.encoder import encode_smiles
            from tantrium.domains.spectral import SpectralMeasure
            obj = encode_smiles(smiles)
            eigs = obj.structure.get("eigenvalues", [])
            if not eigs:
                return None
            n = len(eigs)
            weights = [1.0 / n] * n
            return SpectralMeasure(eigenvalues=eigs, weights=weights, name=smiles[:20])
        except Exception:
            return None

    @staticmethod
    def _target_spec(target: str):
        """Hedef spektral ölçü — SMILES ise moleküler, değilse metin Gram."""
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(target) is not None:
                return _GenesisHelpers._mol_spec(target)
        except Exception:
            pass
        try:
            from tantrium.core.encoder import encode
            from tantrium.domains.spectral import moments_to_spectral
            obj = encode(target)
            return moments_to_spectral([float(m) for m in obj.moments], name=target[:20])
        except Exception:
            return None

    @staticmethod
    def _w2(spec_a, spec_b) -> float:
        from tantrium.domains.spectral import spectral_distance
        if spec_a is None or spec_b is None:
            return float("inf")
        return spectral_distance(spec_a, spec_b)

    # ── Spektral kılavuz: hedeften yapı ipuçları ────────────────────────────

    def _read_spectral_guide(self, moments: list[float]) -> dict:
        """Momentlerden türetilen yapı kılavuzu.

        Bu benzerlik değil — Hamburger momentlerinden matematiksel okuma.
        μ_1 = ortalama eigenvalue → genel yoğunluk
        μ_2/μ_1² > 1 → geniş spektrum → heteroatom/çift bağ
        spectral_rank → efektif bileşen sayısı = karmaşıklık
        """
        from tantrium.core.reconstruct import reconstruct_measure
        try:
            meas = reconstruct_measure(moments)
            rank = meas.rank
            support = meas.support
            weights = meas.weights
        except Exception:
            rank, support, weights = 2, [0.5, 1.0], [0.5, 0.5]

        moments[0] if moments else 1.0
        moments[1] if len(moments) > 1 else 1.0

        # Spektral yayılım: yüksekse heteroatom/aromatik
        spread = float(max(support) - min(support)) if support else 1.0

        # Tahmini atom sayısı: momentlerden
        # μ_1 = Tr(G)/n → n ≈ Tr(G)/μ_1. G normalize edilmiş → Tr(G) ≈ rank
        n_atoms_est = max(3, min(16, round(rank * 3 + spread * 2)))

        # Halka içeriği: spektral gap (en küçük pozitif eigenvalue)
        min_pos = min((s for s in support if s > 0.01), default=0.5)
        # Küçük minimum eigenvalue → daha az bağlı (lineer zincir)
        # Büyük minimum eigenvalue → halka içeriği
        ring_content = min_pos > 0.3

        # Heteroatom ihtiyacı: geniş spektrum + yüksek max eigenvalue
        needs_hetero = spread > 0.8 or max(support) > 1.5

        return {
            "n_atoms": n_atoms_est,
            "ring_content": ring_content,
            "needs_hetero": needs_hetero,
            "rank": rank,
            "spread": spread,
            "support": support,
            "weights": weights,
        }

    @staticmethod
    def _quantum_guide(moments: list[float]) -> dict:
        """Serbest kümülantlardan yapı rehberi — klasik spectral kılavuzun takviyesi.

        κ₄ → halka/dallanma (non-Gaussianity)
        |κ₃| → asimetri → heteroatom ihtiyacı
        """
        try:
            from tantrium.core.quantum_moments import FreeCumulants
            kappa = FreeCumulants.from_moments(moments)
            return {
                "ring_content": kappa.ring_indicator() > 0.08,
                "needs_hetero": kappa.hetero_indicator() > 0.04,
            }
        except Exception:
            return {"ring_content": False, "needs_hetero": False}

    def _quantum_score(self, smi: str, target_moments: list[float], target_spec) -> float:
        """Kuantum-ağırlıklı skor: 0.75×spektral_W2 + 0.25×κ_mesafe.

        Spektral W2 moleküler topolojiyi okur; κ-mesafe yapısal asimetri/halka
        bilgisini ekler. İkisi birlikte daha doğru rehberlik sağlar.
        """
        spec = self._mol_spec(smi)
        if spec is None:
            return float("inf")
        w2 = self._w2(spec, target_spec)
        try:
            from tantrium.core.quantum_moments import FreeCumulants
            mu_smi = [spec.moment(k) for k in range(min(8, len(target_moments)))]
            kd = FreeCumulants.from_moments(mu_smi).distance(
                FreeCumulants.from_moments(target_moments)
            )
        except Exception:
            kd = 0.0
        return 0.75 * w2 + 0.25 * kd

    # ── Beam search: atom-atom inşa ─────────────────────────────────────────

    def _beam_grow(
        self,
        target_moments: list[float],
        target_spec,
        guide: dict,
        max_atoms: int,
        beam_width: int,
        top_k: int,
    ) -> tuple[list[tuple[str, float, int]], int]:
        """Greedy beam search: W2 azaldıkça ilerle.

        Her adımda beam_width en iyi parçayı tut.
        """
        from rdkit import Chem

        # Başlangıç: CC (2 atom) — en küçük anlamlı moleküler Laplacian
        start_smi = "CC"
        start_w2 = self._quantum_score(start_smi, target_moments, target_spec)
        if start_w2 == float("inf"):
            start_spec = self._mol_spec(start_smi)
            if start_spec is None:
                from tantrium.domains.spectral import SpectralMeasure
                start_spec = SpectralMeasure(eigenvalues=[1.0], weights=[1.0], name="CC")
            start_w2 = self._w2(start_spec, target_spec)

        # Beam: [(smiles, w2, steps)]
        beam: list[tuple[str, float, int]] = [(start_smi, start_w2, 0)]
        completed: list[tuple[str, float, int]] = []
        total_steps = 0
        seen: set[str] = {start_smi}

        n_target = guide["n_atoms"]
        ring_content = guide["ring_content"]
        needs_hetero = guide["needs_hetero"]

        prev_best_w2 = start_w2
        stagnant = 0

        for step in range(max_atoms):
            next_beam: list[tuple[str, float, int]] = []

            for base_smi, base_w2, base_steps in beam:
                base_mol = Chem.MolFromSmiles(base_smi)
                if base_mol is None:
                    continue
                n = base_mol.GetNumAtoms()

                # Her boyuttaki adayı tamamlanmış listesine ekle (n≥3)
                if n >= 3:
                    completed.append((base_smi, base_w2, base_steps))

                # Tüm olası genişletmeleri dene
                extensions = self._get_extensions(base_smi, n, ring_content, needs_hetero)
                total_steps += len(extensions)

                for ext_smi in extensions:
                    if ext_smi in seen:
                        continue
                    seen.add(ext_smi)

                    # Kuantum-ağırlıklı skor: spektral W2 + κ-mesafe
                    ext_score = self._quantum_score(ext_smi, target_moments, target_spec)
                    if ext_score == float("inf"):
                        continue
                    next_beam.append((ext_smi, ext_score, base_steps + 1))

            # En iyi beam_width'i tut — W2'ye göre sırala
            next_beam.sort(key=lambda x: x[1])
            beam = next_beam[:beam_width]

            if not beam:
                break

            current_best = beam[0][1]

            # Duraklama tespiti: W2 iyileşmiyorsa dur
            if current_best < prev_best_w2 * 0.995:
                stagnant = 0
                prev_best_w2 = current_best
            else:
                stagnant += 1
                if stagnant >= 3:
                    break

            # Atom sayısı hedefine ulaşıldıysa dur
            if beam and Chem.MolFromSmiles(beam[0][0]) and \
               Chem.MolFromSmiles(beam[0][0]).GetNumAtoms() >= n_target:
                break

        # Son beam adaylarını da ekle
        completed.extend(beam)

        # En iyi top_k * 3'ü seç
        completed.sort(key=lambda x: x[1])
        return completed[:top_k * 3], total_steps

    def _get_extensions(
        self, smiles: str, n_atoms: int, ring_content: bool, needs_hetero: bool
    ) -> list[str]:
        """Mevcut molekülü genişletecek tüm geçerli SMILES'ları üret."""
        from rdkit import Chem
        from rdkit.Chem import Atom

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []

        extensions = []
        atom_types = [6, 7, 8] if needs_hetero else [6]  # C, N, O veya sadece C

        # 1. Zincir uzatma: var olan her atoma yeni atom ekle
        for atom_idx in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(atom_idx)
            if atom.GetTotalNumHs() == 0:
                continue  # Valans dolu

            for atomic_num in atom_types:
                rwmol = Chem.RWMol(mol)
                new_idx = rwmol.AddAtom(Atom(atomic_num))
                rwmol.AddBond(atom_idx, new_idx, Chem.BondType.SINGLE)
                try:
                    Chem.SanitizeMol(rwmol)
                    s = Chem.MolToSmiles(rwmol)
                    if s and len(s) < 80:
                        extensions.append(s)
                except Exception:
                    pass

        # 2. Çift bağ ekleme (eğer halka içeriği düşükse, sp2 yapı dene)
        for atom_idx in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(atom_idx)
            if atom.GetSymbol() == "C" and atom.GetTotalNumHs() >= 2:
                rwmol = Chem.RWMol(mol)
                new_idx = rwmol.AddAtom(Atom(6))
                rwmol.AddBond(atom_idx, new_idx, Chem.BondType.DOUBLE)
                try:
                    Chem.SanitizeMol(rwmol)
                    s = Chem.MolToSmiles(rwmol)
                    if s and len(s) < 80:
                        extensions.append(s)
                except Exception:
                    pass

        # 3. Halka kapama (ring_content True ise)
        if ring_content and n_atoms >= 4:
            for i in range(mol.GetNumAtoms()):
                for j in range(i + 2, mol.GetNumAtoms()):
                    if mol.GetBondBetweenAtoms(i, j) is None:
                        # Halka boyutu kontrolü (5 veya 6)
                        ring_size = abs(i - j) + 1
                        if ring_size in (5, 6):
                            rwmol = Chem.RWMol(mol)
                            rwmol.AddBond(i, j, Chem.BondType.SINGLE)
                            try:
                                Chem.SanitizeMol(rwmol)
                                s = Chem.MolToSmiles(rwmol)
                                if s:
                                    extensions.append(s)
                            except Exception:
                                pass

        return extensions[:16]  # Her adımda maks 16 genişletme

    # ── Sertifika ────────────────────────────────────────────────────────────

    def _certify_all(
        self, raw: list[tuple[str, float, int]], target_moments: list[float]
    ) -> list[GenesisCandidate]:
        from rdkit import Chem

        candidates = []
        seen_smi: set[str] = set()

        for smiles, w2, steps in raw:
            # Kanonik SMILES → tekilleştir
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                canon = Chem.MolToSmiles(mol)
                if canon in seen_smi:
                    continue
                seen_smi.add(canon)
                n_atoms = mol.GetNumAtoms()
            except Exception:
                continue

            # Yapısal sertifika
            paradigms_passed = 0
            paradigms_total = 23
            try:
                run = self.engine.network.run(self.engine.encoder.encode(canon))
                paradigms_passed = run.certified_count
                paradigms_total = run.total
            except Exception:
                pass

            candidates.append(GenesisCandidate(
                smiles=canon,
                moments=[],
                w2=w2,
                paradigms_passed=paradigms_passed,
                paradigms_total=paradigms_total,
                n_atoms=n_atoms,
                steps=steps,
            ))

        return candidates
