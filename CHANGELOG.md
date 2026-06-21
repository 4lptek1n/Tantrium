# Changelog

Bu dosya, `claude/asi-pure-math` branch'inin (durumsuz saf-matematik makinesi)
önemli değişikliklerini kaydeder.

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
