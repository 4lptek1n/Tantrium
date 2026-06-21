"""Üçlü cross (sanal wet-lab) mixin — hastalık × ilaç × kişi DNA'sı → işe yarar mı.

cross_check: ETKİLİLİK (hastalık ⊞ ilaç → DNA tabanı) + UYUMLULUK (ilaç ⊞ DNA
gerçeklenebilir + rezonans). Kişiye-özel κ yargısı → CrossResult.
"""
from __future__ import annotations

from ._types import CrossResult


class _CrossMixin:
    def cross_check(self, disease, drug: str, dna: str) -> "CrossResult":
        """ÜÇLÜ CROSS (sanal wet-lab): hastalık × ilaç × KİŞİNİN DNA'sı → işe yarar mı.

        disease: ölçülen hastalık (moment listesi / bulgu / isim) → κ_disease
        drug   : ilaç (SMILES) → κ_drug
        dna    : kişinin DNA dizisi (ATCG...) → κ_dna  (kişinin sağlıklı tabanı)

        ETKİLİLİK: κ(hastalık ⊞ ilaç) kişinin DNA tabanına (κ_dna) dönüyor mu (Sturm + κ-hata).
        UYUMLULUK: κ(ilaç ⊞ DNA) gerçeklenebilir mi (Hankel-PSD + pürüzsüz Sturm = advers yok).
        Aynı hastalık+ilaç, farklı DNA → farklı yargı (kişiselleştirilmiş).
        """
        from tantrium.core.quantum_moments import (
            FreeCumulants, bounded_kappa_distance)
        from tantrium.core.paradigms import CertifiableObject
        from fractions import Fraction

        # κ_disease (sayı/bulgu/isim), κ_drug (SMILES), κ_dna (kişinin dizisi)
        if isinstance(disease, (list, tuple)) and disease and all(
                isinstance(x, (int, float)) for x in disease):
            kd = FreeCumulants.from_moments([float(x) for x in disease])
        elif isinstance(disease, (list, tuple)):
            kd = FreeCumulants([0.0] * 6)
            for f in disease:
                mu = self._encode(str(f))
                if mu:
                    kd = kd.add(FreeCumulants.from_moments(mu))
        else:
            mu = self._encode(str(disease))
            kd = FreeCumulants.from_moments(mu) if mu else FreeCumulants([0.0] * 6)

        mu_drug = self._encode(str(drug))
        k_drug = FreeCumulants.from_moments(mu_drug) if mu_drug else FreeCumulants([0.0] * 6)
        # DNA ad/dizi → kanonik encode (kişinin sağlıklı tabanı). Genomun dizi yapısını
        # (kompozisyon) moment uzayına çeker → kişiler ayrılır.
        mu_dna = self._encode(str(dna))
        k_dna = FreeCumulants.from_moments(mu_dna) if mu_dna else FreeCumulants([0.0] * 6)
        mu_dna_full = k_dna.to_moments_approx()

        # ETKİLİLİK: hastalık ⊞ ilaç → kişinin DNA tabanı
        treated = kd.add(k_drug)
        mu_treated = treated.to_moments_approx()
        eff_err = bounded_kappa_distance(mu_treated, mu_dna_full, include_mean=True)
        eff_ok_sturm, eff_pivot = self._sturm_path_pivot_min(mu_treated, mu_dna_full)
        efficacy_ok = bool(eff_pivot >= -0.02 and eff_err < 0.5)

        # UYUMLULUK: ilaç ⊞ DNA gerçeklenebilir mi (yapısal) + ilaç↔DNA REZONANSI.
        # Serbest-toplam tek başına hep geçerli (girişim göremez); gerçek kişiye-özel sinyal
        # ilaç ile kişinin DNA'sı arasındaki κ-rezonansıdır: çok DÜŞÜK = ilaç genomu taklit
        # ediyor (mimik/girişim/off-target riski), çok YÜKSEK = alâkasız. Güvenli bir bant var.
        compat = k_drug.add(k_dna)
        mu_compat = compat.to_moments_approx()
        obj = CertifiableObject(
            name="⟨drug+dna⟩",
            moments=[Fraction(x).limit_denominator(10 ** 9) for x in mu_compat])
        compat_psd = obj.is_moment_sequence(size=4)
        _ok2, compat_pivot = self._sturm_path_pivot_min(mu_dna_full, mu_compat)
        resonance = bounded_kappa_distance(mu_drug, mu_dna_full, include_mean=True)
        # girişim riski: ilaç κ'sı kişinin genom κ'sına patolojik yakın (mimik)
        compat_ok = bool(compat_psd and compat_pivot >= -0.02 and resonance >= 0.02)

        # Kişiye-özel YANIT skoru (sıralama için): düşük etkililik-hatası = yüksek yanıt.
        response = max(0.0, min(100.0, 100.0 * (1.0 - eff_err)))

        works = efficacy_ok and compat_ok
        if works:
            verdict = "İŞE YARAR (bu kişide) — etkili ve uyumlu"
        elif not compat_ok:
            verdict = "UYGUNSUZ — bu DNA ile girişim/mimik riski (etkili olsa bile verme)"
        elif not efficacy_ok:
            verdict = "ETKİSİZ — bu kişide hastalığı tabana taşımıyor"
        else:
            verdict = "BELİRSİZ"

        return CrossResult(
            efficacy_pivot=float(eff_pivot), efficacy_error=float(eff_err),
            efficacy_ok=efficacy_ok, compat_hankel_psd=compat_psd,
            compat_pivot=float(compat_pivot), compat_resonance=float(resonance),
            compat_ok=compat_ok, response_score=float(response),
            works=works, verdict=verdict)
