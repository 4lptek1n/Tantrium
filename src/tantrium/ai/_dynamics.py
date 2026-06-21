"""Tantrium AI — dinamik/keşif yüzeyi (DynamicsMixin).

reconstruct / reverse_engineer / discover_law / forecast / detect_anomalies /
quantum_distance / synthesize / entangle / spectrum.
"""
from __future__ import annotations

from ._results import UniverseReconstruction, LawDiscovery


class DynamicsMixin:
    """Ters yön (moment→ölçü), yasa keşfi, tahmin, kuantum moment metotları."""

    def reconstruct(self, query: str, max_atoms: int = 4) -> "object":
        """Ters yön: moment dizisinden ölçüyü GERİ KUR (Gauss kuadratürü / Prony).

        Encoder ileri yön (yapı→moment); bu ters yön (moment→ölçü).
        dμ = Σ wᵢ·δ(x−xᵢ) atomik ölçüsünü geri kurar, sadakati ölçer.
        "Moment yapıyı belirler" iddiasının yapıcı kanıtı — ve üretkenlik.

        Döner: ReconstructedMeasure (support, weights, reconstruction_error, ...)
        """
        from tantrium.core.reconstruct import reconstruct_measure
        obj = self._engine.encoder.encode(query, name=query[:64])
        return reconstruct_measure(obj.moments, max_atoms=max_atoms)

    def reverse_engineer(self, observations, name: str = "fenomen",
                         max_modes: int = 8) -> "UniverseReconstruction":
        """EVRENE TERSİNE MÜHENDİSLİK — gözlemden onu ÜRETEN gizli yapıyı geri çıkar.

        Bir domain DEĞİL, META-güç: drug/material/math bunun örnekleri. Herhangi bir
        fenomen (sayı dizisi · molekül · DNA/protein · sinyal · görüntü · yapı) gözleminden
        onu üreten atomik yapıyı (özdeğer 'modları' = gizli operatör/yasa) geri kurar +
        sertifikalar. Hilbert-Pólya işlevi domain-kör: her şeyin bir Hamiltonian'ı var,
        biz onu GÖZLEMDEN buluyoruz. Evrensel yasayla (F24) girdi gerçek formuyla girer.

        observations: ham gözlem — sayı listesi (ölçüm) / SMILES / DNA / sinyal / metin.
        Döner: UniverseReconstruction (.modes = üreten yapı, .summary()).
        """
        from tantrium.core.reconstruct import reconstruct_measure, reconstruction_fidelity
        from tantrium.core.paradigms import CertifiableObject
        from fractions import Fraction

        # SAYISAL GÖZLEM (sinyal/ölçüm/dizi) → HAM matematik (Kronecker/Prony Hankel rank).
        # Encoder'ın 8-moment sıkıştırmasından GEÇİRMEYİZ (yapıyı siler: 8 moment hep ~4 atom).
        # Ham veriden üreten yapıyı okur — yapılı=düşük rank, gürültü=tam rank, manipüle=rank fırlar.
        if isinstance(observations, (list, tuple)) and observations and all(
                isinstance(x, (int, float)) for x in observations):
            from tantrium.core.structure import structural_decomposition
            x = [float(v) for v in observations]
            sd = structural_decomposition(x, max_modes=max_modes)
            real_modes = [m.real for m in sd.modes if abs(m.imag) < 1e-6]
            return UniverseReconstruction(
                name=str(name),
                signature=[round(v, 6) for v in x[:8]],
                modes=[round(m.real, 6) if abs(m.imag) < 1e-9 else complex(m)
                       for m in sd.modes],
                weights=list(sd.singular_values[:max_modes]),
                n_modes=sd.rank,
                fidelity=float(sd.sv_gap),
                realizable=bool(sd.structured),     # gizli düzen var mı (rank ≪ tam)
                exact=bool(sd.sv_gap > 0.05),        # rank'ta keskin spektral boşluk
            )

        # SEMBOLİK GÖZLEM (molekül/DNA/metin) → evrensel yasayla gerçek-form encode → spektral imza
        try:
            obj = self._engine.encoder.encode_adaptive(observations, name=str(name)[:64])
        except Exception:
            obj = self._engine.encoder.encode(observations, name=str(name)[:64])
        mu = [float(m) for m in obj.moments]
        rec = reconstruct_measure(mu, max_atoms=max_modes)
        try:
            psd = CertifiableObject(
                name=str(name),
                moments=[Fraction(x).limit_denominator(10 ** 9) for x in mu]
            ).is_moment_sequence(size=4)
        except Exception:
            psd = False
        return UniverseReconstruction(
            name=str(name),
            signature=list(mu),
            modes=[float(x) for x in rec.support],
            weights=[float(w) for w in rec.weights],
            n_modes=int(rec.rank),
            fidelity=float(reconstruction_fidelity(mu)),
            realizable=bool(psd),
            exact=bool(rec.well_determined),
        )

    def discover_law(self, observations, name: str = "veri",
                     holdout: int = 4) -> "LawDiscovery":
        """HAM VERİDEN DOĞA YASASI KEŞFİ — hiçbir formül verilmeden, domain-kör.

        Gözlemleri YÖNETEN lineer yineleme + karakteristik kökleri (dinamik modlar) çıkarır
        (Kronecker/Prony), sonra GÖRÜLMEMİŞ kuyruğu tahmin edip doğrular. Keşfet + tahmin =
        sertifika. Fibonacci→altın oran, sönümlü salınım→frekans+sönüm, üstel bozunum→sabit.

        observations: ham sayı dizisi (zaman serisi / ölçüm / dizi).
        holdout     : son kaç değer SAKLANSIN (yasa onları tahmin edip doğrulayacak).
        Döner: LawDiscovery (.summary(); .recurrence = yasa; .forecast = tahmin).
        """
        import numpy as np, math
        from tantrium.core.structure import structural_decomposition
        x = [float(v) for v in observations]
        h = max(0, min(holdout, len(x) - 4))
        fit = x[:len(x) - h] if h else x
        sd = structural_decomposition(fit, tol=1e-6)
        modes = sd.modes
        r = max(1, len(modes))

        # Karakteristik kökler → lineer yineleme katsayıları (x[n]=Σ c_i x[n-i])
        try:
            poly = np.poly(np.array([complex(m) for m in modes]))  # [1,-c1,-c2,...]
            recurrence = [float((-poly[i + 1]).real) for i in range(len(poly) - 1)]
        except Exception:
            recurrence = []

        # Modların yorumu (büyüme/sönüm/salınım)
        dynamics, seen = [], set()
        for m in modes:
            z = complex(m)
            if abs(z.imag) < 1e-6:
                rate = z.real
                if abs(rate - 1) < 1e-4:
                    desc = "sabit mod (λ≈1)"
                elif rate > 0:
                    desc = (f"büyüme oranı λ={rate:.5f}"
                            + (f"  (= altın oran φ!)" if abs(rate - (1 + 5 ** .5) / 2) < 1e-3 else ""))
                    if rate < 1:
                        desc = f"üstel bozunum λ={rate:.5f} (sabit={-math.log(rate):.4f})"
                else:
                    desc = f"salınımlı mod λ={rate:.5f}"
            else:
                if z.imag <= 0:
                    continue
                freq = abs(math.atan2(z.imag, z.real)); decay = -math.log(abs(z))
                key = (round(freq, 4), round(decay, 4))
                if key in seen:
                    continue
                seen.add(key)
                desc = f"salınım: frekans={freq:.4f}, sönüm={decay:.4f}"
            dynamics.append(desc)

        # Keşfedilen yasayla GÖRÜLMEMİŞ geleceği tahmin et + doğrula
        forecast, perr, holds = [], 0.0, False
        if recurrence:
            seq = list(fit)
            k = h if h else 4
            for _ in range(k):
                nxt = sum(c * seq[-(i + 1)] for i, c in enumerate(recurrence))
                seq.append(nxt); forecast.append(nxt)
            if h:
                actual = x[len(x) - h:]
                denom = max(1e-9, max(abs(a) for a in actual))
                perr = sum(abs(f - a) for f, a in zip(forecast, actual)) / (len(actual) * denom)
                holds = perr < 1e-3
            else:
                holds = sd.structured
        return LawDiscovery(
            name=str(name), order=r,
            modes=[round(m.real, 6) if abs(m.imag) < 1e-9 else complex(round(m.real, 4), round(m.imag, 4))
                   for m in modes],
            recurrence=[round(c, 6) for c in recurrence],
            dynamics=dynamics, forecast=forecast,
            predict_error=float(perr), law_holds=bool(holds))

    def forecast(self, series, steps: int = 8, order: int | None = None) -> dict:
        """EVRENSEL TAHMİN — lineer VE nonlineer/kaotik yasaları çözer (en gelişmiş).

        Hem lineer (AR/Prony) hem nonlineer (Koopman/EDMD polinom-NARX) modeli holdout'ta
        yarıştırır, KAZANANI seçer → lojistik-harita gibi kaotik sistemleri de yakalar.
        Domain-kör; sertifika: holdout hatası + reliable. Döner: {forecast, model, order,
        residual_std, holdout_error, reliable}.
        """
        from tantrium.core.structure import (forecast as _fc, nonlinear_forecast as _nl)
        x = [float(v) for v in series]
        h = max(1, min(int(steps), len(x) // 4))

        def _holdout(fn):
            if len(x) - h < 4:
                return None, None
            try:
                pred = fn(x[:len(x) - h], h)[0]
                actual = x[len(x) - h:]
                if not pred:
                    return None, None
                denom = max(1e-9, max(abs(a) for a in actual))
                return sum(abs(p - a) for p, a in zip(pred, actual)) / (len(actual) * denom), pred
            except Exception:
                return None, None

        lin_err, _ = _holdout(lambda s, k: _fc(s, steps=k, order=order))
        nl_err, _ = _holdout(lambda s, k: _nl(s, steps=k, degree=2, embed=3))
        # KAZANANI seç (düşük holdout hatası)
        use_nl = (nl_err is not None and (lin_err is None or nl_err < lin_err))
        if use_nl:
            fut, meta, sigma = _nl(x, steps=steps, degree=2, embed=3)
            model, herr, c = "nonlineer (Koopman/EDMD)", nl_err, meta[0]
        else:
            fut, c, sigma = _fc(x, steps=steps, order=order)
            model, herr = "lineer (AR/Prony)", lin_err
        return {
            "forecast": [round(v, 6) for v in fut],
            "model": model,
            "order": len(c),
            "residual_std": round(sigma, 6),
            "holdout_error": (round(herr, 6) if herr is not None else None),
            "reliable": (herr is not None and herr < 0.05),
        }

    def detect_anomalies(self, series, z: float = 3.0, order: int | None = None) -> dict:
        """EVRENSEL ANOMALİ/SAHTELİK tespiti — 'normal'i bilmeden, yapıdan.

        Veriyi yöneten yasayı bulur; yasaya uymayan noktaları (|kalıntı|>z·σ) işaretler:
        arıza, manipülasyon, dolandırıcılık, olağandışı olay. Yer + şiddet (z-skor) döner.
        Domain-kör: sensör/finans/ağ/biyosinyal. Döner: {anomalies, n, residual_std, clean}.
        """
        from tantrium.core.structure import anomaly_scan
        anomalies, sigma = anomaly_scan([float(v) for v in series], order=order, z=z)
        return {
            "anomalies": anomalies,
            "n": len(anomalies),
            "residual_std": round(sigma, 6),
            "clean": len(anomalies) == 0,
        }

    # ── Kuantum Moment API ────────────────────────────────────────────────────

    def quantum_distance(self, a: str, b: str) -> float:
        """İki kavram/molekül arasındaki kuantum mesafe: (1-γ)×W2 + γ×κ_mesafe.

        Klasik W2 mesafesine serbest kümülant düzeltmesi ekler.
        a, b: kavram adı, metin, SMILES — herhangi girdi.
        """
        from tantrium.core.quantum_moments import QuantumSignature
        mu_a = [float(m) for m in self.engine.encoder.encode(a).moments]
        mu_b = [float(m) for m in self.engine.encoder.encode(b).moments]
        return QuantumSignature.from_moments(mu_a).quantum_distance(
            QuantumSignature.from_moments(mu_b)
        )

    def synthesize(self, concept_a: str, concept_b: str) -> str:
        """Serbest toplam: κ_A + κ_B → manifolddaki en yakın kavram.

        Voiculescu serbest bileşke: κ(A ⊕ B) = κ(A) + κ(B).
        İki kavramın kuantum bileşkesine en yakın manifold noktasını bulur.
        a, b: kavram adı, metin veya SMILES.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        ka = FreeCumulants.from_moments(
            [float(m) for m in self.engine.encoder.encode(concept_a).moments]
        )
        kb = FreeCumulants.from_moments(
            [float(m) for m in self.engine.encoder.encode(concept_b).moments]
        )
        k_sum = ka.add(kb)
        approx_mu = k_sum.to_moments_approx()
        hits = self.engine.manifold._nearest_quantum_vec(approx_mu, top_k=5)
        if not hits:
            return f"'{concept_a}' + '{concept_b}' için manifoldda eşleşme bulunamadı"
        name, dist = hits[0]
        return f"Serbest bileşke: '{name}'  (kuantum mesafe: {dist:.4f})"

    def entangle(self, concept_a: str, concept_b: str) -> dict:
        """Kuantum dolanıklık testi: klasik uzak ama kuantum yakın mı?

        Klasik mesafe yüksek + κ-mesafe düşük → gizli matematiksel bağlantı.
        Döner: {classical_dist, quantum_dist, kappa_dist, entangled, note}
        """
        from tantrium.core.quantum_moments import QuantumSignature
        from tantrium.core.metric import l1_distance
        mu_a = [float(m) for m in self.engine.encoder.encode(concept_a).moments]
        mu_b = [float(m) for m in self.engine.encoder.encode(concept_b).moments]
        sig_a = QuantumSignature.from_moments(mu_a)
        sig_b = QuantumSignature.from_moments(mu_b)
        entangled = sig_a.is_entangled_with(sig_b)
        return {
            "classical_dist": round(l1_distance(mu_a, mu_b), 5),
            "quantum_dist":   round(sig_a.quantum_distance(sig_b), 5),
            "kappa_dist":     round(sig_a.cumulants.distance(sig_b.cumulants), 5),
            "entangled": entangled,
            "note": "Gizli matematiksel bağlantı" if entangled else "Normal ayrışma",
        }

    def spectrum(self, query: str) -> "object":
        """Girdinin spektral ölçüsü: G=AᵀA → özdeğer dağılımı dμ = Σwᵢδ(λ-λᵢ).

        Hamburger: bounded support → dμ ↔ {μₖ} birebir (TAV sabit noktası unique).
        8 moment gölgesi değil — operatörün kendisi.

        Döner: SpectralMeasure (eigenvalues, entropy(), gap(), effective_rank(), ...)
        """
        from tantrium.domains.spectral import moments_to_spectral
        obj = self._engine.encoder.encode(query, name=query[:64])
        return moments_to_spectral([float(m) for m in obj.moments], name=query[:64])
