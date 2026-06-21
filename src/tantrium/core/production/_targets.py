"""Hedef okuma mixin — girdiyi (SMILES/protein/hastalık/bulgu) κ-hedefine çevirir.

_read_target / _read_target_ext / _deconvolve_to_target / _read_findings.
Hepsi ProductionEngine'in self._encode / self._is_smiles / self._reference_ligands /
self._disease_drivers / self._canonical_kappa yardımcılarını kullanır (mixin birleşik).
"""
from __future__ import annotations


class _TargetReadingMixin:
    # ── Hedef okuma ────────────────────────────────────────────────────────

    def _read_target(self, target: str
                     ) -> tuple[str, list[float], list[list[float]], str]:
        """Geriye-uyum: _read_target_ext'in ilk dört öğesi."""
        kind, mu_req, profiles, ref, *_ = self._read_target_ext(target)
        return kind, mu_req, profiles, ref

    def _read_target_ext(self, target: str, network: bool = False
                         ) -> tuple[str, list[float], list[list[float]], str,
                                    float | None, object | None, object | None]:
        """Hedefi oku → 7-tuple: (kind, mu_req, profiles, ref, gap, κ_dis, κ_hlt).

        SMILES     : κ_disease=sıfır, κ_healthy=κ(hedef SMILES). gap=None.
        Protein    : bilinen ligand profillerinden; κ_disease=sıfır, κ_healthy=ligand κ-ort. gap=None.
        Hastalık   : ters dekonvolüsyon; gap=gerçeklenebilirlik hatası (≥0).
        """
        from tantrium.core.quantum_moments import FreeCumulants
        kzero = FreeCumulants([0.0] * 6)

        if self._is_smiles(target):
            mu = self._encode(target)
            kh = FreeCumulants.from_moments(mu)
            return "smiles", mu, [mu], f"hedef yapı {target[:20]}", None, kzero, kh

        refs = self._reference_ligands(target)
        if refs:
            profile = []
            for _nm, smi in refs:
                mu = self._encode(smi)
                if mu:
                    profile.append(mu)
            if profile:
                avg = [sum(p[i] for p in profile) / len(profile)
                       for i in range(len(profile[0]))]
                kh = FreeCumulants.from_moments(avg)
                return "protein", avg, profile, f"{len(refs)} bilinen ligand", None, kzero, kh

        # HASTALIK = moleküler sürücüleri (metin DEĞİL, ÖLÇÜM). Hastalığı süren druggable
        # hedeflerin (KRAS yerine egfr/braf/...) ligand-kimyasını κ-topla → hastalığın
        # GERÇEK matematiksel imzası. "İlaç matematikten gelir": hastalığın ölçülen
        # yapısından çözüm doğar. Eskiden "pancreatic cancer" METNİ encode edilip glukoz
        # çıkıyordu (anlamsız imza → pivot<0). Şimdi sürücülerden ölçülür.
        drivers = self._disease_drivers(target)
        if drivers:
            # Birincil druggable sürücüyü hedefle: çok-sürücü ortalaması κ-hedefini
            # bulanıklaştırıp jenerik molekül veriyordu. Tek tutarlı sürücü (en çok
            # ligandlı) → gerçek inhibitör (EGFR-sürücülü kanser → EGFR-sınıfı inhibitör).
            profile: list[list[float]] = []
            used: list[str] = []
            best_lig: list[tuple[str, str]] = []
            primary = drivers[0]
            for drv in drivers:
                ligs = self._reference_ligands(drv)
                if len(ligs) > len(best_lig):
                    best_lig, primary = ligs, drv
                used.append(drv)
            for _nm, smi in best_lig:
                mu = self._encode(smi)
                if mu:
                    profile.append(mu)
            if profile:
                avg = [sum(p[i] for p in profile) / len(profile)
                       for i in range(len(profile[0]))]
                kh = FreeCumulants.from_moments(avg)
                ref = (f"birincil sürücü: {primary} ({len(profile)} ligand) | "
                       f"tüm sürücüler: {', '.join(used)} (ölçülen hastalık)")
                # Ölçüm artık ligand-profili (sürücülerin inhibitör kimyası) — protein
                # yoluyla AYNI: M, profili eşlesin → gerçek inhibitör (gefitinib-sınıfı),
                # jenerik κ-eşleşmesi (kafein) değil. profiles=tüm ligandlar → strateji havuzu zengin.
                return "protein", avg, profile, ref, None, kzero, kh

        mu_d = self._encode(target)
        if not mu_d:
            return "invalid", [], [], "", None, None, None

        kd = FreeCumulants.from_moments(mu_d)
        kh = self._canonical_kappa()
        mu_req, gap = self._deconvolve_to_target(kd, kh)

        return "disease", mu_req, [mu_req], "kanonik sağlıklı denge (ζ + wild-type)", gap, kd, kh

    def _deconvolve_to_target(self, kd, kh) -> tuple[list[float], float]:
        """κ_healthy ⊟ κ_disease → düzeltici ilaç imzası mu_req (+ gerçeklenebilirlik gap).

        İlaç = hastalığı sağlıklıya taşıyan serbest-konvolüsyon tersi: κ_M = κ_healthy ⊟ κ_disease.
        Negatif moment (gerçeklenemez ölçü) → reconstruct ile en yakın GERÇEK ölçüye düş;
        gap = o düşüşün hatası (büyükse hastalık imzası tek molekülle düzeltilemez — DÜRÜST sinyal).
        Hem hastalık-adı hem ÖLÇÜLEN-BULGU yolu bunu paylaşır (tek dekonvolüsyon çekirdeği).
        """
        kappa_req = kh.subtract(kd)
        mu_req_raw = kappa_req.to_moments_approx()
        if any(x < -1e-6 for x in mu_req_raw[1:]):
            try:
                from tantrium.core.reconstruct import reconstruct_measure
                rm = reconstruct_measure(mu_req_raw)
                return (list(rm.reconstructed_moments[:len(mu_req_raw)]),
                        float(rm.reconstruction_error))
            except Exception:
                mu = [max(0.0, x) for x in mu_req_raw]
                if mu:
                    mu[0] = 1.0
                return mu, float("inf")
        return mu_req_raw, 0.0

    def _read_findings(self, findings: list
                       ) -> tuple[str, list[float], list[list[float]], str,
                                  float | None, object | None, object | None]:
        """Hastalığı ÖLÇÜLEN BULGUDAN oku — AD YOK, sözlük araması YOK.

        Bulgu = hastalık durumunu karakterize eden ölçülmüş moleküler sinyaller:
        dysregüle metabolit (SMILES) · mutasyon (DNA) · aşırı-aktif protein (dizi) ·
        biyobelirteç · ham sinyal. Her bulgu AYNI moment uzayına çekilir, serbest-toplam
        (κ-additivite) → κ_disease = hastalığın GERÇEK matematiksel imzası. İlaç =
        κ_healthy ⊟ κ_disease'i kapatan M (de novo inşa). Bellekte OLMAYAN hastalık →
        yakın ad değil, kendi bulgusu ölçülür; üretilen molekül de hiç olmayan olabilir.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        kd = FreeCumulants([0.0] * 6)
        used = 0
        for f in findings:
            mu = self._encode(str(f))
            if mu:
                kd = kd.add(FreeCumulants.from_moments(mu))
                used += 1
        if used == 0:
            return "invalid", [], [], "", None, None, None
        kh = self._canonical_kappa()
        mu_req, gap = self._deconvolve_to_target(kd, kh)
        ref = f"ölçülen bulgu ({used} sinyal → κ_disease serbest-toplam)"
        return "findings", mu_req, [mu_req], ref, gap, kd, kh
