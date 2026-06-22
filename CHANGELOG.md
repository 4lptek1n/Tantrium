# Changelog

Bu dosya, `claude/asi-pure-math` branch'inin (durumsuz saf-matematik makinesi)
önemli değişikliklerini kaydeder.

## [0.3.0] — 46-boyutlu operatif birim + Cosmos omurgası + spektral sınıf

### Eklenenler
- `cosmos.py` — ★ **Cosmos yaşam-döngüsü omurgası:** bir tohumu T₀ Yasa → T₁ encode →
  T₂ Ouroboros genişleme → T₃ 23-paradigma → T₄ madde → T₅ kendini-örgütleme →
  T₆ kritik çizgi → T₇ Achilles → T₈ mühür → T₉ serbest kümülant → T₁₀ μ*/patlama
  çağlarından geçirir; tek mühürlü `Lifecycle`. SDK: `ai.cosmos(seed)`.
- `core/fixed_point.py` — öz-gönderim sabit noktası μ* (makine kendine bakar; 45-dim imza
  uzayında, 46 RH-merceğinde kapanış). `self_reference_orbit`, SDK `ai.self_reference()`.
- `core/spectral_class.py` — ★ **integrallenebilir↔kaotik** dedektörü: TAM N×N spektrumun
  seviye-aralığı ⟨r⟩'si (8 moment DEĞİL). Bohigas-Giannoni-Schmit + Berry-Tabor; Poisson
  (kapalı-form) / GOE (kaotik). SDK: `ai.spectral_class(query)`.
- `metric.certificate_vector/certificate_distance/full_distance` + SDK `ai.fingerprint`/`ai.compare`.
- `tools/ouroboros.py`, `tools/ouroboros_explosion.py` — kendi kendini besleyen genişleme +
  kendini-örgütleme (etkin rank doyar) + kondisyon patlaması (gerçek ufuk).

### Değişenler
- ★ **TAM 46-boyutlu sertifika operatif birim oldu (8 momente/W2'ye çökme).** `metric.distance()`
  varsayılanı 46-dim; W2 yalnız `metric="w2"`. "En yakını seç/hedefe mesafe" yargısı veren tüm
  yollar buna bağlandı (inverse / molecular_space / genesis / certifier). Çökme tasarımca olan
  yerler korundu (collision moment-testi, transport dyadic/Sturm, concept convergence).
- Kanıt: cache'li 46-dim (0.032ms) W2'den (0.045ms) hem daha ayırt edici hem daha hızlı;
  W2 aspirin/kafeini ≈0'a çökerken 46-dim onları ayırır.

## [0.2.0] — Saf-matematik çekirdeği + RH matematiğinin tam entegrasyonu

### Eklenenler — RH ispat matematiği (tce-collapse-engine'den türetildi)
- `core/rh_criteria.py` — momentlerden τ (Hankel/subdiscriminant) / pivot (LDLᵀ-Sturm) /
  cross-ratio / Stieltjes / klasik kümülant / de Bruijn-Newman Λ / **rank** (exact Fraction).
- `core/jensen.py` — Jensen-Pólya hiperbolisite (Laguerre-Pólya / RH-tipi kriter), Turán/Laguerre.
- `core/free_probability.py` — Voiculescu serbest entropi χ, R-dönüşümü, serbest konvolüsyon, yarı-daire.
- `core/bezoutian.py` — Bezoutian gizli faktörler, Lah-pivot referansı (d−j)², Gate-B merdiven yasası.
- `core/verifier.py` — mühürlü sertifika (SHA-256), tamper-tespiti, adversarial kontrol.
- `core/rh_certificate.py` — ★ TÜM moment-RH matematiğini tek `RHCertificate`'te birleştirir;
  encoder her çıktıya `structure["rh"]`, CoreMachine her sertifikaya RH bundle + mühür taşır.

### Değişenler
- **Tam ASI prototipi saf-matematik çekirdeğine indirgendi:** dil / kod ajanı / öğrenilen graf /
  manifold / büyüme / reasoning / meta / perception katmanları silindi. `ai.py` 6206 → mixin paketi.
- `serve.py` REST yüzeyi saf-matematiğe göre yeniden yazıldı (certify/rh/transport/seal/verify...).
- `transport.rank_candidates` durumsuz + RH-mesafe sıralamalı.
- CoreMachine `coherent` verdict'i RH-Stieltjes kapısı içerir (geçersiz/artefakt eler).

### Kanıt
- Adversarial ayrım benchmark'ı (`tools/discrimination_benchmark.py`): 6/6 → **DISCRIMINATES**.

### Altyapı
- Alakasız JS/TS satış-app monorepo'su kaldırıldı; kök tertemiz.
- CI/CD (GitHub Actions: 3.10–3.12 + ruff + pytest), profesyonel `pyproject.toml`, LICENSE.
- 500+ satırlık 7 monolit aynı-isimli paketlere bölündü (public API korunarak).
- Felsefi isimler gerçek isimlere (`codex→paradigms`, `CodexObject→CertifiableObject`...).
- Ruff lint 180 → 0; ~290 test geçiyor.
