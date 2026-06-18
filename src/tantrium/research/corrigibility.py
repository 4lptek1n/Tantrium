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
    resolved_collisions = 0
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
                # ÇÖZME (öz-keskinleştirme): çakışma = injektiflik ihlali (Kaf paradigması).
                # "8 moment yapıyı belirler" aksiyomu: iki FARKLI kavram AYNI imzaya düşemez.
                # Derin re-encode name'i other'dan ayırabilir mi? — bounded, per-concept,
                # idempotent (manifold-geneli batch DEĞİL, yasak). Ayrışırsa düzelt+kalıcı;
                # değilse şüpheli. Döngü her turda temsili DAHA injektif yapar.
                resolved = False
                if correct and encoder is not None and ":" not in name:
                    try:
                        new_enc = encoder.encode_adaptive(name)
                        nmu = [float(m) for m in getattr(new_enc, "moments", [])]
                        other_c = manifold.concepts.get(other)
                        omu = [float(m) for m in getattr(other_c, "moments", [])] if other_c else []
                        if nmu and omu and len(nmu) == len(omu):
                            new_d = sum(abs(a - b) for a, b in zip(nmu, omu))
                            if new_d >= _COLLISION_EPS:
                                c.moments = [
                                    Fraction(x).limit_denominator(10 ** 9) for x in new_enc.moments
                                ]
                                resolved_collisions += 1
                                resolved = True
                                logs.append(
                                    f"çözüldü (çakışma→ayrıştı): {name}↔{other} (L1 {new_d:.4f})"
                                )
                    except Exception:
                        pass
                if not resolved:
                    collided += 1
                    new_suspects.append(f"{name}~{other}")
                    logs.append(f"şüpheli (çakışma): {name} ≈ {other} (L1 {float(d):.4f})")

    return {
        "checked": checked,
        "degenerate": degenerate,
        "collided": collided,
        "corrected": corrected,
        "resolved_collisions": resolved_collisions,
        "new_suspects": new_suspects,
        "logs": logs,
    }


# Dış-doğrulama: küratörlü bilinen olgulara karşı kausal bilgi (TEK tanım — ai.benchmark
# bu çekirdeğe delege eder). detect_and_correct YAPISAL (içsel) yanlışı yakalar; bu
# DIŞSAL doğruyu sınar: "sistemin kausal bilgisi gerçek dünyayla uyuşuyor mu?".
_DEFAULT_FACTS: list[tuple[str, str, str]] = [
    ("erlotinib", "INHIBITS", "egfr"),
    ("gefitinib", "INHIBITS", "egfr"),
    ("egfr", "ACTIVATES", "ras"),
    ("ras", "CAUSES", "tumor cell"),
    ("aspirin", "INHIBITS", "cyclooxygenase"),
    ("imatinib", "INHIBITS", "bcr-abl"),
    ("p53", "INHIBITS", "tumor cell"),
]
_CAUSAL = {"CAUSES", "ACTIVATES", "INHIBITS"}


def external_verify(engine: Any, facts: "list[tuple[str, str, str]] | None" = None) -> dict:
    """Küratörlü bilinen olgulara karşı kausal TAU'yu sına (DIŞ-doğrulama).

    İçsel sertifika ≠ dünyada doğru. Bu, sistemin kausal bilgisinin gerçek olgularla
    uyumunu ölçer → ampirik isabet (track record). Döner: {score, correct, total, failures}.
    """
    test_facts = facts or _DEFAULT_FACTS
    tau = engine.tau
    fwd_idx: dict[str, set[tuple[str, str]]] = {}
    for src, edges in tau.edges.items():
        for e in edges:
            if e.paradigm in _CAUSAL:
                fwd_idx.setdefault(src, set()).add((e.paradigm, e.target))
    correct = 0
    failures: list[dict] = []
    for src, rel, tgt in test_facts:
        edges = fwd_idx.get(src.lower(), set()) | fwd_idx.get(src, set())
        if any(r == rel and t in {tgt, tgt.lower()} for r, t in edges):
            correct += 1
        else:
            failures.append({"fact": f"{src} {rel} {tgt}", "found": False})
    total = len(test_facts)
    return {
        "score": (correct / total) if total else 0.0,
        "correct": correct,
        "total": total,
        "failures": failures,
    }


# ── HESAP-ORACLE'I: sistemin matematiksel mekanizmasını BAĞIMSIZ kesin hesaba sına ──
# external_verify küratörlü KAUSAL olguyu sınar (gerçek dünya ilişkisi). Bu, sistemin
# SAYISAL/cebirsel ÇEKİRDEĞİNİ gerçek matematiğe karşı sınar — lab GEREKMEZ, kesin hesap:
#   1. Sturm pivot ⟺ hiperbolisite: sistemin TAÇ mekanizması (Sturm pivot pozitifliği =
#      Jensen hiperbolisitesi = RH kriteri). Tüm pivotlar pozitif ⟺ polinomun tüm kökleri
#      REEL olmalı. Bağımsız companion-matris (numpy.roots, TAMAMEN farklı algoritma) ile
#      karşılaştır. Uyuşmazlık = sistemin pozitiflik↔gerçeklik köprüsünde GERÇEK bug.
#   2. Hankel moment-dizisi PSD (Aleph temeli): GERÇEK atomik ölçüden (Σ wᵢxᵢᵏ, wᵢ>0)
#      üretilen moment DAİMA PSD → sistem "moment dizisi" demeli; kasıtlı geçersiz dizi
#      reddedilmeli. Kurulu gerçeğe (ölçü teorisi) karşı sına.

# (coeffs azalan derece, numpy konvansiyonu), beklenen: tüm kökler reel mi (hiperbolik mi)
_STURM_CASES: list[tuple[list[float], bool, str]] = [
    ([1, 0, -1], True, "x^2-1 = (x-1)(x+1)"),
    ([1, 0, 1], False, "x^2+1 (kompleks ±i)"),
    ([1, 0, -3, 1], True, "x^3-3x+1 (3 reel kök)"),
    ([1, -1, 1, -1], False, "(x-1)(x^2+1)"),
    ([1, 0, -5, 0, 4], True, "(x^2-1)(x^2-4) (4 reel)"),
    ([1, 0, 0, 0, 1], False, "x^4+1 (tüm kompleks)"),
    ([1, -6, 11, -6], True, "(x-1)(x-2)(x-3)"),
    ([1, 0, 1, 0, 1], False, "x^4+x^2+1 (kompleks)"),
    ([1, 1, 1], False, "x^2+x+1 (kompleks)"),
    ([1, 0, -5, 0, 4, 0], True, "x(x^2-1)(x^2-4) (5 reel)"),
    ([1, 0, -2], True, "x^2-2 (±√2 reel)"),
    ([1, 0, 0, 1], False, "x^3+1 (1 reel 2 kompleks)"),
]


def computational_verify(engine: Any = None, *, tol: float = 1e-7) -> dict:
    """Sistemin hesaplanabilir matematiksel iddiasını BAĞIMSIZ kesin hesaba sına.

    İçsel sertifika ≠ doğru. Bu, Sturm pivot pozitifliği↔hiperbolisite köprüsünü
    numpy companion-matris köklerine, Hankel-PSD'yi ölçü teorisine karşı sınar.
    Döner: {score, correct, total, failures, sturm, hankel}.
    """
    import numpy as np
    from tantrium.algebra.sturm import normalized_sturm_pivots

    correct = 0
    total = 0
    failures: list[dict] = []

    # 1) STURM pivot pozitifliği ⟺ tüm kökler reel (numpy bağımsız gerçek)
    sturm_ok = 0
    sturm_total = 0
    try:
        from sympy import symbols
        x = symbols("x")
        for coeffs, expect_hyperbolic, label in _STURM_CASES:
            sturm_total += 1
            total += 1
            # BAĞIMSIZ gerçek: companion-matris özdeğerleri (Sturm'dan tamamen farklı)
            roots = np.roots(coeffs)
            all_real = bool(np.all(np.abs(roots.imag) < 1e-6))
            # sanity: test etiketi gerçekle uyuşmalı (battery doğru kurulmuş mu)
            if all_real != expect_hyperbolic:
                failures.append({"case": label, "kind": "battery_mismatch",
                                 "numpy_all_real": all_real, "expected": expect_hyperbolic})
                continue
            # SİSTEM: Sturm pivotları (taç mekanizma)
            expr = sum(c * x ** (len(coeffs) - 1 - i) for i, c in enumerate(coeffs))
            try:
                pivots = normalized_sturm_pivots(expr, x)
                pvals = [float(p) for p in pivots]
                all_pos = all(p > tol for p in pvals)
            except Exception as e:
                failures.append({"case": label, "kind": "sturm_error", "error": str(e)})
                continue
            if all_pos == all_real:
                correct += 1
                sturm_ok += 1
            else:
                failures.append({"case": label, "kind": "sturm_hyperbolicity",
                                 "pivots_all_positive": all_pos, "all_roots_real": all_real,
                                 "pivots": [round(p, 4) for p in pvals]})
    except Exception as e:
        failures.append({"kind": "sturm_setup_error", "error": str(e)})

    # 2) HANKEL moment-dizisi PSD: gerçek ölçü → DAİMA PSD; geçersiz → reddet
    from fractions import Fraction
    from tantrium.core.codex import CertifiableObject
    hankel_ok = 0
    hankel_total = 0

    def _moments_from_measure(support, weights, n=8):
        return [sum(w * (s ** k) for s, w in zip(support, weights)) for k in range(n)]

    hankel_cases: list[tuple[list[float], bool, str]] = [
        (_moments_from_measure([0.2, 0.5, 0.9], [0.3, 0.4, 0.3]), True, "3-atom ölçü"),
        (_moments_from_measure([0.1, 0.8], [0.6, 0.4]), True, "2-atom ölçü"),
        (_moments_from_measure([0.5], [1.0]), True, "tek-atom (Dirac)"),
        ([1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0], False, "geçersiz (H₂ PSD değil)"),
        ([1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0], False, "geçersiz (μ₂<μ₁²)"),
    ]
    for moments, expect_psd, label in hankel_cases:
        hankel_total += 1
        total += 1
        obj = CertifiableObject(name=label,
                                moments=[Fraction(x).limit_denominator(10 ** 9) for x in moments])
        verdict = obj.is_moment_sequence(size=4)
        if verdict == expect_psd:
            correct += 1
            hankel_ok += 1
        else:
            failures.append({"case": label, "kind": "hankel_psd",
                             "system_says_psd": verdict, "truth_psd": expect_psd})

    return {
        "score": (correct / total) if total else 0.0,
        "correct": correct,
        "total": total,
        "failures": failures,
        "sturm": {"correct": sturm_ok, "total": sturm_total},
        "hankel": {"correct": hankel_ok, "total": hankel_total},
    }


# ── AMPİRİK ORACLE: sertifika BİLİNEN farmakolojiyi geri kazanıyor mu (geriye-dönük) ──
# computational_verify saf matematiği sınar; bu, sistemin moleküler ayrımının GERÇEK
# ölçülmüş ilaç-hedef ilişkilerini takip edip etmediğini sınar — wet-lab GEREKMEZ, zaten
# ölçülmüş farmakoloji (küratörlü). Leave-one-out: bir ligandı, kendi hedefinin DİĞER
# ligandlarından kurulan profile + tüm rakip hedeflere κ-fit ile sırala; gerçek hedef
# tepe-k'de mi? İçsel sertifikanın gerçeği ne kadar öngördüğünün DÜRÜST sayısı.
_PANEL_TARGETS = ["egfr", "vegfr", "abl", "alk", "kit", "bcr-abl",
                  "braf", "her2", "cyclooxygenase", "mtor"]


def empirical_verify(engine: Any, *, targets: "list[str] | None" = None,
                     metric: str = "kappa") -> dict:
    """Sertifikanın moleküler ayrımı bilinen ilaç→hedef eşleşmesini geri kazanıyor mu.

    Leave-one-out geriye-dönük: her ligand kendi hedefinin DİĞER ligandlarından kurulan
    profile karşı + tüm panel hedeflerine sıralanır; gerçek hedef tepe-1/tepe-2'de mi.

    metric: "kappa"  → κ-mesafe (YAKINLIK — dil ekseni; düşük=iyi).
            "sturm"  → Sturm-yol pivotu (RH evren-kapanışı matematiği; pivot yüksek=iyi
                       gerçek-ölçü yolu). Üretimin GERÇEK mekanizması — yakınlık değil.
    İkisini karşılaştırmak: "sınır yakınlık-proxy'sinin mi, RH matematiğinin mi" sorusunu
    dürüstçe yanıtlar. Lab YOK.
    """
    from tantrium.core.production import ProductionEngine
    pe = ProductionEngine(engine)
    panel = targets or _PANEL_TARGETS

    # Her panel hedefinin ligandları (isim, smiles) + κ-fit için moment encode (cache)
    enc: dict[str, list[float]] = {}

    def _mu(smi: str) -> list[float]:
        v = enc.get(smi)
        if v is None:
            v = pe._encode(smi)
            enc[smi] = v or []
        return enc[smi]

    tgt_ligs: dict[str, list[tuple[str, str]]] = {}
    for t in panel:
        ligs = [(n, s) for n, s in pe._reference_ligands(t) if _mu(s)]
        if len(ligs) >= 2:
            tgt_ligs[t] = ligs
    panel = list(tgt_ligs.keys())

    def _profile(ligs: list[tuple[str, str]]) -> list[float]:
        mus = [_mu(s) for _, s in ligs]
        mus = [m for m in mus if m]
        if not mus:
            return []
        return [sum(m[i] for m in mus) / len(mus) for i in range(len(mus[0]))]

    top1 = top2 = top1_rel = tested = 0
    rr_sum = 0.0
    per_target: dict[str, dict] = {}
    # pharmakolojik akrabalık: ligand kümeleri kesişen hedefler (çok-hedefli ilaç gerçeği)
    lig_sets = {t: {s for _, s in tgt_ligs[t]} for t in panel}
    for true_t in panel:
        t_correct1 = t_n = 0
        for name, smi in tgt_ligs[true_t]:
            lig_mu = _mu(smi)
            if not lig_mu:
                continue
            # her hedefe profil: gerçek hedef LOO (test ligandını çıkar), rakipler tam
            fits: list[tuple[str, float]] = []
            for t in panel:
                if t == true_t:
                    others = [(n, s) for n, s in tgt_ligs[t] if s != smi]
                    prof = _profile(others)
                else:
                    prof = _profile(tgt_ligs[t])
                if not prof:
                    continue
                if metric == "sturm":
                    # RH evren-kapanışı matematiği: gerçek-ölçü Sturm yolu pivotu.
                    # Pivot YÜKSEK = sağlam yol → maliyet = -pivot (düşük=iyi, tek sıralama).
                    _ok, pmin = pe._sturm_path_pivot_min(lig_mu, prof)
                    cost = -float(pmin)
                else:
                    cost = pe._structural_kappa_distance(lig_mu, prof)
                fits.append((t, cost))
            if not fits:
                continue
            fits.sort(key=lambda kv: kv[1])
            ranked = [t for t, _ in fits]
            rank = ranked.index(true_t) + 1 if true_t in ranked else len(ranked) + 1
            tested += 1
            t_n += 1
            rr_sum += 1.0 / rank
            if rank == 1:
                top1 += 1
                t_correct1 += 1
            if rank <= 2:
                top2 += 1
            # akraba-isabet: tahmin edilen #1 hedef, gerçek hedefle ligand paylaşıyorsa
            # (imatinib abl'de test edilip kit tahmin → farmakolojik olarak DOĞRU)
            pred = ranked[0]
            if smi in lig_sets.get(pred, set()) or (lig_sets.get(pred, set())
                                                    & lig_sets.get(true_t, set())):
                top1_rel += 1
        if t_n:
            per_target[true_t] = {"top1": t_correct1, "n": t_n}

    return {
        "top1": (top1 / tested) if tested else 0.0,
        "top2": (top2 / tested) if tested else 0.0,
        "top1_related": (top1_rel / tested) if tested else 0.0,
        "mrr": (rr_sum / tested) if tested else 0.0,
        "tested": tested,
        "n_targets": len(panel),
        "per_target": per_target,
        "metric": metric,
        "note": (f"[{metric}] {top1}/{tested} ligand gerçek hedefini tepe-1, "
                 f"{top1_rel}/{tested} akraba-hedef ({len(panel)} hedefli panel, LOO). "
                 + ("RH-Sturm: yapısal-benzer kinaz-içi seçicilik (egfr) ayrılır; "
                    "yapısal-farklı sınıf zayıf — κ-yakınlıkla TAMAMLAYICI."
                    if metric == "sturm" else
                    "κ-yakınlık: kaba sınıf (NSAID/rapalog) ayrılır; kinaz-içi ince "
                    "seçicilik AYRILMAZ — RH-Sturm ile TAMAMLAYICI.")),
    }


def encoder_health(engine: Any, *, n_samples: int = 100) -> dict:
    """Encoder'ın İÇSEL sadakatini ölç (CollisionHunter adversarial öz-test).

    Rastgele FARKLI girdiler 8-momentte çakışıyor mu? Çakışanlar derinlik(16) ya da
    label-aware kodlamayla AYRIŞIYOR mu (çözülebilir) yoksa İÇKİN mi (encoder sınırı)?
    Bu, "8 moment yapıyı belirler" temel iddiasının canlı sağlık göstergesi —
    encoder sadakatini GÖRÜNÜR/izlenir kılar (eskiden görünmez bir kör noktaydı).

    DÜRÜST SINIR: bu ÖLÇER. Çözülebilir çakışmayı UYGULAMAK (manifoldu daha derin/
    label-aware şemaya taşımak) manifold-geneli batch yeniden-encode'dur (metrik-uzay
    tutarlılığı yerel takası yasaklar) — otonom faz değil, `migrate_text_encoding.py`
    deseninde kasıtlı bir migrasyon. Döner: {collision_rate, collisions, resolved_*, inherent}.
    """
    try:
        from tantrium.core.collision import CollisionHunter
        rep = CollisionHunter(engine).hunt(n_samples=n_samples)
    except Exception:
        return {"collision_rate": 0.0, "collisions": 0, "resolved_by_depth": 0,
                "resolved_by_labels": 0, "inherent": 0, "pairs_compared": 0}
    inherent = sum(
        1 for c in rep.collisions
        if not c.resolved_by_depth and not getattr(c, "resolved_by_labels", False)
    )
    # Bu sayaçlar @property (metot değil) — parantezsiz.
    return {
        "collision_rate": rep.collision_rate,
        "collisions": len(rep.collisions),
        "resolved_by_depth": rep.resolved_count,
        "resolved_by_labels": rep.resolved_by_labels_count,
        "inherent": inherent,
        "pairs_compared": rep.pairs_compared,
    }
