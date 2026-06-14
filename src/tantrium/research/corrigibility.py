"""Corrigibility — temsil hatası tespiti + düzeltme (PAYLAŞILAN çekirdek).

GIMEL (`pipeline.stage_l5_gimel`, argmin_paradigma margin) içsel GÖRELİ zayıflığı
bulur ama hata ÜNİFORM olduğunda (protein/glucose: G=PᵀP=I → μ_k≡1, bütün marjinler
tekdüze iyi) göremez — temsil yine de yanlıştır. Bu modül o kör noktayı kapatır;
iki yapısal yanlış-sinyalini GIMEL'den bağımsız okur:

  1. DEJENERE encoding: moment yayılımı (max−min) < _DEGEN_SPREAD
     (faithful Hausdorff dizisi azalır; tekdüze = temsil çökmüş) → adaptif re-encode.
  2. ÇAKIŞMA: en yakın FARKLI kavram L1 < _COLLISION_EPS (neredeyse-tam çakışma,
     saturasyon değil gerçek ayırma hatası) → işaretle.

growth (akış döngüsü `_verify_consolidate`) ve cognition (batch döngüsü `VerifyPhase`)
AYNI çekirdeği çağırır — tek tanım, tek davranış (defter ilkesi: parçaları birleştir).
"""
from __future__ import annotations

from typing import Any

# Eşikler (tek tanım — growth da buradan import eder)
_DEGEN_SPREAD = 0.02     # moment yayılımı bunun altında = dejenere encoding
_COLLISION_EPS = 0.001   # iki FARKLI kavram bu L1 altında = çakışma şüphesi
_VERIFY_MAX = 60         # döngü başına denetlenen kavram (maliyet sınırı)
_VERIFY_COLLISION_MAX = 20  # çakışma taraması O(N) — daha sıkı sınır


def detect_and_correct(
    engine: Any,
    seen: set[str],
    *,
    max_per_pass: int = _VERIFY_MAX,
    collision_max: int = _VERIFY_COLLISION_MAX,
    correct: bool = True,
) -> dict:
    """Manifoldda dejenere/çakışan temsilleri TESPİT et, dejenereyi DÜZELT.

    seen: caller'ın sahip olduğu "denetlendi" kümesi (artımlı, oturum/döngü boyu).
    correct: dejenere encoding'i adaptif re-encode ile düzeltmeyi dene.
    Döner: {checked, degenerate, collided, corrected, new_suspects, logs}.
    Düzelmeyen dejenere + çakışmalar `new_suspects`'te (caller kalıcı hafızaya alır).
    """
    from fractions import Fraction

    manifold = engine.manifold
    encoder = getattr(engine, "encoder", None)
    checked = degenerate = collided = corrected = 0
    collision_scans = 0
    new_suspects: list[str] = []
    logs: list[str] = []

    for name, c in list(manifold.concepts.items()):
        if checked >= max_per_pass:
            break
        if name in seen or name.startswith("⟨"):
            continue
        mu = [float(m) for m in getattr(c, "moments", [])]
        if len(mu) < 2:
            continue
        seen.add(name)
        checked += 1
        spread = max(mu) - min(mu)

        # 1) DEJENERE encoding (üniform moment = protein/glucose sınıfı)
        if spread < _DEGEN_SPREAD:
            degenerate += 1
            fixed = False
            # 2) DÜZELT: adaptif derin re-encode (yalnız düz/SMILES isim;
            #    oeis:/algo:/theorem: önekte yanlış-düzeltmeyi önlemek için işaretle)
            if correct and encoder is not None and ":" not in name:
                try:
                    new_enc = encoder.encode_adaptive(name)
                    nmu = [float(m) for m in getattr(new_enc, "moments", [])]
                    if nmu and (max(nmu) - min(nmu)) >= _DEGEN_SPREAD:
                        c.moments = [
                            Fraction(x).limit_denominator(10 ** 9) for x in new_enc.moments
                        ]
                        corrected += 1
                        fixed = True
                        logs.append(
                            f"düzeltildi: {name} dejenere→ayrıştı "
                            f"(yayılım {max(nmu) - min(nmu):.3f})"
                        )
                except Exception:
                    pass
            if not fixed:
                new_suspects.append(name)
                logs.append(f"şüpheli (dejenere, düzeltilemedi): {name}")
            continue

        # 3) ÇAKIŞMA: en yakın FARKLI kavram çok yakınsa (O(N) — sınırlı)
        if collision_scans >= collision_max:
            continue
        collision_scans += 1
        try:
            hits = manifold.nearest(c, n=1, metric="l1")
        except Exception:
            hits = []
        if hits:
            other, d = hits[0]
            if other != name and float(d) < _COLLISION_EPS:
                collided += 1
                new_suspects.append(f"{name}~{other}")
                logs.append(f"şüpheli (çakışma): {name} ≈ {other} (L1 {float(d):.4f})")

    return {
        "checked": checked,
        "degenerate": degenerate,
        "collided": collided,
        "corrected": corrected,
        "new_suspects": new_suspects,
        "logs": logs,
    }
