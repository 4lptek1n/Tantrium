#!/usr/bin/env python3
"""Ayrım (Discrimination) Benchmark — Tantrium'un GERÇEKTEN ayırt ettiğinin kanıtı.

Dokümanlanmış #1 açık soru:
    "23 paradigma her şeyi geçirir (G=AᵀA daima PSD) — gerçekten AYIRT EDİYOR MU?"

Cevap (bu benchmark kanıtlar): EVET — pozitiflik verdictleri çoğu girdide geçse de
RH-sertifika VEKTÖRÜ (rank / Stieltjes / Hausdorff / grade / κ / pivot) ile mühürlü
seal/verify + adversarial negatif kontrol birlikte AYIRT EDİCİDİR.

Kanıtlanan 6 ayrım özelliği:
  1. Gerçek ilaçlar Stieltjes/Hamburger-sertifikalı + sonlu rank.
  2. rank AYIRT EDİCİ: simetrik/küçük (benzen) düşük rank, ilaçlar yüksek rank.
  3. rh_distance metriği tutarlı: d(x,x)=0; kimyasal çift < ilaç-vs-rastgele-çöp.
  4. Adversarial negatif kontrol: Hankel-PSD-olmayan dizi DÜRÜSTÇE NOT_CERTIFIED.
  5. Mühür denetlenebilir: seal→verify=VERIFIED; kurcalanmış→TAMPERED.
  6. Çapa ayrımı: kanonik dağılımlar (ZETA_ZEROS, GUE, ...) farklı sertifika üretir.

Kullanım:
    python tools/discrimination_benchmark.py
"""
from __future__ import annotations

import copy
from typing import Any

import tantrium


# ── Kanonik girdiler ─────────────────────────────────────────────────────────
DRUGS = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "caffeine": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "paracetamol": "CC(=O)Nc1ccc(O)cc1",
    "benzene": "c1ccccc1",
}
# Deterministik "molekül-değil" çöp string (encoder imza-momentine gider, kimya YOK).
GARBAGE = "not a molecule at all 42"


def _ok(cond: bool) -> str:
    return "PASS" if cond else "FAIL"


# ── Özellik 1: gerçek ilaçlar sertifikalı + sonlu rank ───────────────────────
def prop1_drugs_certified(ai) -> dict[str, Any]:
    rows = {}
    all_pass = True
    for name, smi in DRUGS.items():
        c = ai.rh_certificate(smi)
        certified = bool(c.stieltjes or c.criteria.hamburger_certified)
        finite_rank = c.rank >= 1
        passed = certified and finite_rank
        all_pass = all_pass and passed
        rows[name] = {
            "rank": c.rank,
            "stieltjes": c.stieltjes,
            "hamburger": c.criteria.hamburger_certified,
            "grade": round(c.grade, 3),
            "pass": passed,
        }
    return {"result": _ok(all_pass), "detail": rows}


# ── Özellik 2: rank AYIRT EDİCİ (benzen < ilaçlar) ──────────────────────────
def prop2_rank_discriminates(ai) -> dict[str, Any]:
    ranks = {n: ai.rh_certificate(s).rank for n, s in DRUGS.items()}
    benzene = ranks["benzene"]
    drug_min = min(ranks[n] for n in DRUGS if n != "benzene")
    strict = benzene < drug_min  # kesin eşitsizlik
    return {
        "result": _ok(strict),
        "detail": {
            "ranks": ranks,
            "benzene_rank": benzene,
            "min_drug_rank": drug_min,
            "inequality": f"benzene({benzene}) < min_drug_rank({drug_min})",
            "strict_holds": strict,
        },
    }


# ── Özellik 3: rh_distance metriği tutarlı ──────────────────────────────────
def prop3_distance_consistent(ai) -> dict[str, Any]:
    asp = DRUGS["aspirin"]
    ibu = DRUGS["ibuprofen"]
    caf = DRUGS["caffeine"]

    d_self = ai.rh_distance(asp, asp)               # = 0
    d_chem = ai.rh_distance(ibu, caf)               # iki gerçek molekül
    d_garbage = ai.rh_distance(ibu, GARBAGE)        # molekül vs rastgele çöp

    identity = d_self == 0.0
    # kimyasal yapı, rastgele stringden ayrışır: gerçek çift, çöpten daha yakın
    chem_clusters = d_chem < d_garbage
    passed = identity and chem_clusters
    return {
        "result": _ok(passed),
        "detail": {
            "d(asp,asp)": d_self,
            "d(ibu,caffeine)": round(d_chem, 4),
            "d(ibu,GARBAGE)": round(d_garbage, 4),
            "identity_zero": identity,
            "inequality": f"d(ibu,caf)={d_chem:.3f} < d(ibu,garbage)={d_garbage:.3f}",
            "chem_clusters": chem_clusters,
        },
    }


# ── Özellik 4: adversarial negatif kontrol ──────────────────────────────────
def prop4_adversarial_control(ai) -> dict[str, Any]:
    ac = tantrium.adversarial_control()
    honest = (
        ac["certification_status"] == "NOT_CERTIFIED"
        and ac["honest_rejection"] is True
        and ac["hankel_psd"] is False
    )
    return {
        "result": _ok(honest),
        "detail": {
            "input": ac["input_repr"],
            "hankel_psd": ac["hankel_psd"],
            "certification_status": ac["certification_status"],
            "named_gap": ac["named_gap"],
            "honest_rejection": ac["honest_rejection"],
        },
    }


# ── Özellik 5: mühür denetlenebilirliği ─────────────────────────────────────
def prop5_seal_auditable(ai) -> dict[str, Any]:
    sealed = ai.seal(DRUGS["aspirin"])
    clean = ai.verify(sealed)

    tampered = copy.deepcopy(sealed)
    tampered["moments"][0] = "999999"
    tamper = ai.verify(tampered)

    passed = clean["result"] == "VERIFIED" and tamper["result"] == "TAMPERED"
    return {
        "result": _ok(passed),
        "detail": {
            "clean_verify": clean["result"],
            "tampered_verify": tamper["result"],
            "seal_hash": sealed["content_hash"][:16],
        },
    }


# ── Özellik 6: çapa (anchor) ayrımı ─────────────────────────────────────────
def prop6_anchor_discrimination(ai) -> dict[str, Any]:
    from tantrium.core.rh_certificate import certify_rh, rh_distance
    from tantrium.graph.anchors import build_anchor_concepts

    anchors = {c.name: c for c in build_anchor_concepts()}
    zeta = next(c for n, c in anchors.items() if "ZETA" in n)
    gue = next(c for n, c in anchors.items() if "GUE" in n)
    gauss = next(c for n, c in anchors.items() if "GAUSS" in n)

    cz = certify_rh(zeta.moments)
    cg = certify_rh(gue.moments)
    ca = certify_rh(gauss.moments)

    # farklı mühür + sıfırdan büyük çapalar-arası mesafe = ayrışıyorlar
    distinct_hash = len({cz.sealed_hash, cg.sealed_hash, ca.sealed_hash}) == 3
    d_zg = rh_distance(zeta.moments, gue.moments)
    d_za = rh_distance(zeta.moments, gauss.moments)
    separated = d_zg > 0 and d_za > 0
    passed = distinct_hash and separated
    return {
        "result": _ok(passed),
        "detail": {
            "ZETA_ZEROS": {"rank": cz.rank, "semicircle": round(cz.semicircle_distance, 4),
                           "seal": cz.sealed_hash[:12]},
            "GUE": {"rank": cg.rank, "semicircle": round(cg.semicircle_distance, 4),
                    "seal": cg.sealed_hash[:12]},
            "GAUSSIAN": {"rank": ca.rank, "semicircle": round(ca.semicircle_distance, 4),
                         "seal": ca.sealed_hash[:12]},
            "d(ZETA,GUE)": round(d_zg, 4),
            "d(ZETA,GAUSS)": round(d_za, 4),
            "distinct_seals": distinct_hash,
        },
    }


PROPERTIES = [
    ("1_drugs_certified", "Gerçek ilaçlar Stieltjes/Hamburger-sertifikalı + sonlu rank",
     prop1_drugs_certified),
    ("2_rank_discriminates", "rank ayırt edici: benzen < ilaçlar",
     prop2_rank_discriminates),
    ("3_distance_consistent", "rh_distance: d(x,x)=0 ve kimyasal çift < ilaç-vs-çöp",
     prop3_distance_consistent),
    ("4_adversarial_control", "negatif kontrol: geçersiz dizi DÜRÜSTÇE NOT_CERTIFIED",
     prop4_adversarial_control),
    ("5_seal_auditable", "mühür: seal→VERIFIED, kurcalanmış→TAMPERED",
     prop5_seal_auditable),
    ("6_anchor_discrimination", "çapalar (ZETA/GUE/Gauss) farklı sertifika",
     prop6_anchor_discrimination),
]


def run() -> dict[str, Any]:
    """Tüm ayrım özelliklerini çalıştır, özet rapor döndür (her biri PASS/FAIL + kanıt)."""
    ai = tantrium.AI()
    report: dict[str, Any] = {"properties": {}, "summary": {}}
    n_pass = 0
    for key, desc, fn in PROPERTIES:
        out = fn(ai)
        out["description"] = desc
        report["properties"][key] = out
        if out["result"] == "PASS":
            n_pass += 1
    report["summary"] = {
        "passed": n_pass,
        "total": len(PROPERTIES),
        "all_pass": n_pass == len(PROPERTIES),
        "verdict": "DISCRIMINATES" if n_pass == len(PROPERTIES) else "INCOMPLETE",
    }
    return report


def _print_report(report: dict[str, Any]) -> None:
    import json

    print()
    print("  " + "=" * 70)
    print("  TANTRIUM AYRIM (DISCRIMINATION) BENCHMARK")
    print("  Soru: 23 paradigma her şeyi geçirir mi, yoksa GERÇEKTEN ayırt mı eder?")
    print("  " + "=" * 70)
    print()
    for key, desc, _ in PROPERTIES:
        p = report["properties"][key]
        mark = "[OK]" if p["result"] == "PASS" else "[!!]"
        print(f"  {mark} {p['result']:4}  {key}")
        print(f"         {desc}")
        for line in json.dumps(p["detail"], ensure_ascii=False, indent=2).splitlines():
            print("         " + line)
        print()
    s = report["summary"]
    print("  " + "-" * 70)
    print(f"  SONUC: {s['passed']}/{s['total']} ayrim ozelligi PASS  -->  {s['verdict']}")
    print("  " + "-" * 70)
    print()


if __name__ == "__main__":
    rep = run()
    _print_report(rep)
    raise SystemExit(0 if rep["summary"]["all_pass"] else 1)
