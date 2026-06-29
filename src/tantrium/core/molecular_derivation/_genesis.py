"""Moleküler Genesis — MolecularGenesis çekirdek sınıfı.

Hedef → momentler → spektral imza → atom atom inşa.
Her adımda: W2(yeni_molekül, hedef) azalıyorsa ekle, artıyorsa dur.

Çekirdek giriş noktaları (generate / simulate) burada; kodlama/spektral/beam
yardımcıları _helpers._GenesisHelpers mixin'inde.
"""
from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

from ._helpers import _GenesisHelpers
from ._types import GenesisReport, SimStep, SimulationReport

warnings.filterwarnings("ignore")
logging.getLogger("rdkit").setLevel(logging.CRITICAL)
try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


class MolecularGenesis(_GenesisHelpers):
    """Hedef momentlerinden atom-atom molekül türetme.

    Her adımda W2(partial_mol, target) izlenir.
    Azalıyorsa → devam. Artıyorsa veya platoya giriyorsa → dur.
    Bu 'benzerine bak' değil — 'matematiğin zorunlu kıldığı yapıyı kur'.
    """

    def __init__(self, engine: "CertificationEngine"):
        self.engine = engine

    # ── Ana giriş noktası ────────────────────────────────────────────────────

    def generate(
        self,
        target: str,
        top_k: int = 6,
        max_atoms: int = 18,
        beam_width: int = 4,
    ) -> GenesisReport:
        import time
        t0 = time.time()

        target_moments, target_type = self._encode_target(target)
        # Spektral ölçü: SMILES ise moleküler eigenvalue, metin ise Gram moments
        target_spec = self._target_spec(target)
        if target_spec is None:
            from tantrium.domains.spectral import moments_to_spectral
            target_spec = moments_to_spectral(target_moments, name=target[:20])

        # Spektral imzadan başlangıç kılavuzu çıkar + serbest kümülant takviyesi
        guide = self._read_spectral_guide(target_moments)
        q_guide = self._quantum_guide(target_moments)
        # Kuantum rehberi spectral rehberi sertleştirir (override değil, OR)
        if q_guide["ring_content"]:
            guide["ring_content"] = True
        if q_guide["needs_hetero"]:
            guide["needs_hetero"] = True

        # Beam search: atom-atom inşa
        candidates, total_steps = self._beam_grow(
            target_moments=target_moments,
            target_spec=target_spec,
            guide=guide,
            max_atoms=max_atoms,
            beam_width=beam_width,
            top_k=top_k,
        )

        # 23 paradigma sertifika
        certified = self._certify_all(candidates, target_moments)
        certified.sort(key=lambda c: c.w2)

        best = certified[0] if certified else None

        return GenesisReport(
            target=target,
            target_moments=target_moments,
            candidates=certified[:top_k],
            best=best,
            duration_s=round(time.time() - t0, 1),
            total_steps=total_steps,
        )

    # ── Evren simülasyonu: transport ile molekül dizilimi ────────────────────

    def simulate(
        self,
        seed: str = "CC",
        max_steps: int = 18,
        beam_width: int = 5,
        toward: str | None = None,
        toward_profile: list[list[float]] | None = None,
        seeds: list[str] | None = None,
    ) -> "SimulationReport":
        """Makineyi çalıştırarak molekülü transport ile diz — hafıza araması YOK.

        Her atom-ekleme adımı CertifiedTransport ile yargılanır:
          sturm-PSD  → yol gerçek ölçü manifoldunda mı (hayali ara nokta yok) — SERT GEÇİT
          dyadic     → tam rasyonel kütle örtüşmesi (sertifikalı gerçek adım) — TERCİH bonusu
          zeta       → Riemann ζ ailesine derinlik (sürekli yön)

        Sert dyadic geçidi her heteroatomu eler (üretim alkana çöker); bu yüzden
        dyadic bir bonustur, sturm geçittir, zeta yöndür. Beam çeşitliliği
        (en iyi hetero + en iyi halka uçları korunur) çöküşü engeller.

        toward verilirse o SMILES'a doğru W2 ikincil yön olarak eklenir.
        toward_profile (referans ligand moment vektörleri) verilirse KAPALI DÖNGÜ:
        makine bu kuantum (κ) profile doğru büyür — biyolojik yön. Transport+sturm
        gerçeklik geçidi, κ-profil yön. Böylece makine 'işe yarayan bölgeye' ilerler.
        """
        import time

        from rdkit import Chem

        from tantrium.core.encoder import encode
        from tantrium.core.quantum_moments import FreeCumulants
        from tantrium.core.transport import CertifiedTransport

        t0 = time.time()
        ct = CertifiedTransport(self.engine)

        toward_moments = None
        if toward is not None:
            try:
                toward_moments = [float(m) for m in encode(toward).moments]
            except Exception:
                toward_moments = None

        # Kapalı döngü: referans ligand κ-imzaları (biyolojik yön hedefi)
        profile_kappa: list[FreeCumulants] = []
        if toward_profile:
            for mu in toward_profile:
                try:
                    profile_kappa.append(FreeCumulants.from_moments([float(x) for x in mu]))
                except Exception:
                    continue

        from tantrium.core.metric import paradigm_distance
        _enc_cache: dict[str, object] = {}
        # Hedef yapı bir kez hesaplanır (tam 46-boyutlu sertifika için)
        _toward_struct = (encode([float(x) for x in toward_moments], name="toward").structure
                          if toward_moments is not None else None)

        def _enc(smi: str):
            o = _enc_cache.get(smi)
            if o is None:
                o = encode(smi)
                _enc_cache[smi] = o
            return o

        _tw_cache: dict[str, float] = {}

        def _step_cert(base_obj, ext_smi: str) -> SimStep | None:
            try:
                ext_obj = _enc(ext_smi)
                tc = ct.certify(base_obj, ext_obj, fast_sturm=True)
                m = Chem.MolFromSmiles(ext_smi)
                n_atoms = m.GetNumAtoms() if m else 0
                return SimStep(
                    smiles=ext_smi, n_atoms=n_atoms,
                    certified=tc.certified, dyadic=tc.dyadic_verified,
                    sturm=tc.sturm_verified, zeta=tc.zeta_distance,
                    cost=tc.transport_cost,
                )
            except Exception:
                return None

        _kp_cache: dict[str, float] = {}

        def _kappa_to_profile(smi: str) -> float:
            """Adayın κ-imzasının referans profile en yakın mesafesi (biyolojik yön)."""
            if not profile_kappa:
                return 0.0
            v = _kp_cache.get(smi)
            if v is None:
                try:
                    kc = FreeCumulants.from_moments(
                        [float(x) for x in _enc(smi).moments])
                    v = min(kc.distance(pk) for pk in profile_kappa)
                except Exception:
                    v = float("inf")
                _kp_cache[smi] = v
            return v

        def _score(s: SimStep) -> tuple:
            tw = 0.0
            if _toward_struct is not None:
                tw = _tw_cache.get(s.smiles)
                if tw is None:
                    try:
                        # Tam 46-boyut: adayın cache'li GERÇEK yapısı vs hedef yapı
                        tw = paradigm_distance(_enc(s.smiles).structure, _toward_struct)
                    except Exception:
                        tw = 0.0
                    _tw_cache[s.smiles] = tw
            if profile_kappa:
                # KAPALI DÖNGÜ: 1) κ-profile yakınlık (biyolojik yön — birincil)
                #   2) sertifikalı transport adımı (gerçeklik)  3) toward-W2
                # (ζ kaldırıldı — durumsuz makinede inf, sıralamaya katkısı yok = ölü eksen)
                return (_kappa_to_profile(s.smiles), 0 if s.certified else 1, tw)
            # Açık keşif: 1) sertifikalı  2) toward-W2  (ölü ζ tiebreaker kaldırıldı)
            return (0 if s.certified else 1, tw)

        # Tohum(lar): tek atom-zinciri VEYA kimyasal primitif kümesi (halkalar).
        # Çoklu tohum makinenin ilaç uzayına ulaşmasını sağlar — primitif atom kadar
        # temel; cevap molekülü DEĞİL, makine onu primitiften inşa eder.
        seed_list = [s for s in (seeds or [seed]) if Chem.MolFromSmiles(s) is not None]
        if not seed_list:
            seed_list = ["CC"]
        beam: list[SimStep] = []
        seen: set[str] = set()
        for sd in seed_list:
            seen.add(sd)
            beam.append(SimStep(
                smiles=sd, n_atoms=Chem.MolFromSmiles(sd).GetNumAtoms(),
                certified=True, dyadic=True, sturm=True, zeta=0.0, cost=0.0))
        # κ-profil varsa tohumları da profile yakınlığa göre sırala
        if profile_kappa:
            beam.sort(key=lambda s: _kappa_to_profile(s.smiles))
        lineage: list[SimStep] = [beam[0]]
        certified_steps = 0
        total_steps = 0

        for _ in range(max_steps):
            cands: list[SimStep] = []
            for base in beam:
                base_obj = _enc(base.smiles)
                exts = self._get_extensions(
                    base.smiles, base.n_atoms, ring_content=True, needs_hetero=True)
                total_steps += len(exts)
                for ext in exts:
                    if ext in seen:
                        continue
                    seen.add(ext)
                    st = _step_cert(base_obj, ext)
                    if st is None or not st.sturm:
                        continue  # sturm = sert geçit: gerçek olmayan yolu ele
                    cands.append(st)

            if not cands:
                break

            cands.sort(key=_score)

            # Beam çeşitliliği: en iyi N + en iyi hetero + en iyi halka uçları
            def _has_hetero(smi: str) -> bool:
                return any(c in smi for c in "NOSFnos") or "Cl" in smi
            def _has_ring(smi: str) -> bool:
                return any(ch.isdigit() for ch in smi)

            chosen: list[SimStep] = cands[:beam_width]
            for pred in (_has_hetero, _has_ring):
                if not any(pred(s.smiles) for s in chosen):
                    extra = next((s for s in cands if pred(s.smiles)), None)
                    if extra is not None:
                        chosen.append(extra)

            beam = chosen
            best_step = cands[0]
            lineage.append(best_step)
            if best_step.certified:
                certified_steps += 1

        # En DERİN sertifikalı uç (en çok büyümüş = en çok atom). Eskiden min(ζ) ile
        # seçiliyordu; durumsuz makinede ζ=inf olup tohumu (ζ=0) gerçek moleküllere
        # tercih ediyordu (ölü-eksen bug'ı). Artık gerçek derinlik (n_atoms) ile.
        cert_ends = [s for s in beam if s.certified] or beam
        best = max(cert_ends, key=lambda s: s.n_atoms) if cert_ends else None

        return SimulationReport(
            seed=seed,
            lineage=lineage,
            frontier=beam,
            best=best,
            certified_steps=certified_steps,
            total_steps=total_steps,
            duration_s=round(time.time() - t0, 1),
        )
