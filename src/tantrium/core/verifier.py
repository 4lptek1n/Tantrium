"""Independent, read-only sealed-certificate verifier — Tantrium dürüstlük çekirdeği.

Bu modül `origin/tce-collapse-engine:tools/independent_verifier.py`'nin en güçlü
dürüstlük özelliğini izole eder: **mühürlü, bağımsız yeniden-denetlenebilir sertifika**.
SHA-256 içerik-hash zinciri ile sertifikalar kurcalama-tespit edilebilir (tamper-evident),
ve kasıtlı NEGATİF kontrol (tce'nin Goldbach `BLOCKED_BY_NAMED_GAP`'i gibi) makinenin her
girdiyi "geçirmediğini" — geçersiz bir moment dizisini DÜRÜSTÇE `NOT_CERTIFIED` işaretlediğini
— kanıtlar.

Tasarım ilkeleri (tce sadakati):
  * Verifier ÜRETMEZ — yalnız okur ve doğrular (read-only).
  * Kanoniklik: `json.dumps(..., sort_keys=True, separators=(",",":"))` → bit-bit
    tekrarlanabilir, denetlenebilir hash. Aynı girdi → aynı hash, daima.
  * Tüm moment'ler exact-Fraction string olarak serialize edilir (yuvarlama yok).
  * Negatif kontrol (`adversarial_control`) = tce'nin Goldbach minor-arc gap mantığının
    izole karşılığı: bilinen-geçersiz girdinin DÜRÜSTÇE reddedildiğini gösterir.

İzole modül: `ai.py` / `__init__.py`'ye bağımlı değildir (lazy import). Yalnız
`tantrium.core.rh_criteria.rh_criteria` ve `hashlib`/`json`/`fractions` kullanır.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Any, Callable, Sequence

SEAL_VERSION = "tantrium-seal-1"


# ── kanoniklik ────────────────────────────────────────────────────────────────
def _canonical_json(payload: Any) -> str:
    """Bit-bit tekrarlanabilir kanonik JSON (sort_keys + ayraçsız compact)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _content_hash(payload: Any) -> str:
    """SHA-256 over canonical JSON — kurcalama-tespit içerik mührü."""
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _moments_to_strs(moments: Sequence) -> list[str]:
    """Momentleri exact-Fraction string'e serialize et (yuvarlama yok)."""
    out: list[str] = []
    for m in moments:
        if isinstance(m, Fraction):
            out.append(str(m))
        else:
            try:
                out.append(str(Fraction(m)))
            except (TypeError, ValueError):
                out.append(str(m))
    return out


# ── 1. seal ──────────────────────────────────────────────────────────────────
def seal(
    name: str,
    input_repr: str,
    moments: Sequence,
    criteria_dict: dict,
) -> dict:
    """Kanonik, deterministik mühürlü sertifika üret.

    Girdiyi (moments exact-Fraction str), RH-kriterlerini ve verdictleri kanonik
    JSON'a serialize edip SHA-256 içerik-hash'i ekler. Bit-bit tekrarlanabilir:
    aynı (name, input_repr, moments, criteria_dict) → aynı `content_hash`.

    Döner: {"name","input_repr","moments","rh_criteria","content_hash","version"}.
    """
    body = {
        "name": name,
        "input_repr": input_repr,
        "moments": _moments_to_strs(moments),
        "rh_criteria": criteria_dict,
        "version": SEAL_VERSION,
    }
    content_hash = _content_hash(body)
    sealed = dict(body)
    sealed["content_hash"] = content_hash
    return sealed


# ── 2. verify ────────────────────────────────────────────────────────────────
def verify(
    sealed: dict,
    recompute_fn: Callable[[Sequence], dict] | None = None,
) -> dict:
    """Mührü bağımsız doğrula (read-only).

    (a) `content_hash`'i kanonik gövdeden yeniden hesapla — eşleşmeli (tamper-tespiti).
    (b) `recompute_fn` verilirse, mühürlü momentlerden rh_criteria'yı YENİDEN üret ve
        verdictlerin tutarlılığını kontrol et. recompute_fn(moments) → criteria_dict.

    Döner: {"hash_ok":bool,"verdicts_consistent":bool,"result":...}
      result ∈ {"VERIFIED","TAMPERED","INCONSISTENT"}.
    """
    body = {
        "name": sealed.get("name"),
        "input_repr": sealed.get("input_repr"),
        "moments": sealed.get("moments"),
        "rh_criteria": sealed.get("rh_criteria"),
        "version": sealed.get("version"),
    }
    recomputed_hash = _content_hash(body)
    hash_ok = recomputed_hash == sealed.get("content_hash")

    verdicts_consistent = True
    if recompute_fn is not None:
        try:
            moments = [Fraction(s) for s in sealed.get("moments", [])]
        except (TypeError, ValueError):
            moments = list(sealed.get("moments", []))
        fresh = recompute_fn(moments)
        sealed_crit = sealed.get("rh_criteria", {}) or {}
        # Sadece verdict (boolean) eksenlerini karşılaştır — bunlar makinenin
        # "CERTIFIED mi?" kararıdır; sayısal alanlar exact tekrarlanmalı ama
        # tutarlılık verdict düzeyinde tanımlıdır.
        verdict_keys = [
            "hankel_psd", "stieltjes_psd", "pivots_positive",
            "cross_ratio_positive", "first_five_positive",
            "hamburger_certified", "stieltjes_certified",
        ]
        for k in verdict_keys:
            if k in sealed_crit and k in fresh:
                if bool(sealed_crit[k]) != bool(fresh[k]):
                    verdicts_consistent = False
                    break

    if not hash_ok:
        result = "TAMPERED"
    elif not verdicts_consistent:
        result = "INCONSISTENT"
    else:
        result = "VERIFIED"

    return {
        "hash_ok": hash_ok,
        "verdicts_consistent": verdicts_consistent,
        "result": result,
    }


# ── recompute helper (izole; encoder'a bağımlı değil) ─────────────────────────
def _recompute_criteria(moments: Sequence) -> dict:
    """Momentlerden rh_criteria'yı yeniden üret → as_dict. verify(recompute_fn=...) için."""
    from tantrium.core.rh_criteria import rh_criteria
    return rh_criteria(moments).as_dict()


# ── 3. adversarial_control (kasıtlı NEGATİF kontrol) ──────────────────────────
def adversarial_control() -> dict:
    """Kasıtlı negatif kontrol — tce'nin Goldbach `BLOCKED_BY_NAMED_GAP`'inin izole eşi.

    Geçersiz (Hankel PSD OLMAYAN) bir moment dizisi seçer; mühürler; bağımsız doğrular;
    sistemin bunu DÜRÜSTÇE "Hamburger ✗ / NOT_CERTIFIED" işaretlediğini kanıtlar.

    μ = [1, 0, -1, 0, -1, ...]: μ_0=1, μ_2=-1 → H^{(1)}=[[1,0],[0,-1]], det=-1<0.
    Negatif Hankel determinantı = geçersiz moment dizisi (hiçbir pozitif ölçüye karşılık
    gelmez). Makine bunu pozitif diye GEÇİRİRSE dürüst değildir. Bu kontrol, geçirmediğini
    (NOT_CERTIFIED) ispatlar — "her şey PSD" suçlamasına karşı dürüstlük kanıtı.

    Döner: kontrol raporu (verdict + verify sonucu + dürüstlük PASS/FAIL).
    """
    invalid_moments = [
        Fraction(1), Fraction(0), Fraction(-1), Fraction(0),
        Fraction(-1), Fraction(0), Fraction(-1), Fraction(0),
    ]
    criteria = _recompute_criteria(invalid_moments)

    sealed = seal(
        name="ADVERSARIAL_NEGATIVE_CONTROL",
        input_repr="invalid_moments[1,0,-1,0,-1,0,-1,0] (Hankel NOT PSD)",
        moments=invalid_moments,
        criteria_dict=criteria,
    )
    verify_report = verify(sealed, recompute_fn=_recompute_criteria)

    hankel_psd = bool(criteria.get("hankel_psd"))
    hamburger = bool(criteria.get("hamburger_certified"))
    stieltjes = bool(criteria.get("stieltjes_certified"))
    certified = hamburger or stieltjes
    cert_status = "CERTIFIED" if certified else "NOT_CERTIFIED"

    # Dürüstlük: geçersiz girdi REDDEDİLMELİ (NOT_CERTIFIED) VE mühür tutarlı doğrulanmalı.
    honest = (not certified) and (not hankel_psd) and verify_report["result"] == "VERIFIED"

    return {
        "control_kind": "INTENTIONAL_NEGATIVE_CONTROL",
        "analogy": "tce-collapse-engine goldbach BLOCKED_BY_NAMED_GAP",
        "input_repr": sealed["input_repr"],
        "moments": sealed["moments"],
        "hankel_psd": hankel_psd,
        "hamburger_certified": hamburger,
        "stieltjes_certified": stieltjes,
        "certification_status": cert_status,
        "named_gap": "HANKEL_NOT_PSD",
        "seal_verify_result": verify_report["result"],
        "honest_rejection": honest,
        "result": "PASS" if honest else "FAIL",
        "content_hash": sealed["content_hash"],
    }


# ── 4. tamper_test ───────────────────────────────────────────────────────────
def tamper_test(sealed: dict) -> bool:
    """Mühürlü sertifikada bir momenti değiştir → verify "TAMPERED" dönmeli.

    Döner: True ⇔ kurcalama doğru tespit edildi (verify == "TAMPERED").
    """
    tampered = dict(sealed)
    tampered["moments"] = list(sealed.get("moments", []))
    if tampered["moments"]:
        original = tampered["moments"][0]
        # Bir momenti deterministik olarak değiştir (content_hash'i bozar).
        tampered["moments"] = list(tampered["moments"])
        tampered["moments"][0] = original + "0" if isinstance(original, str) else original
        if tampered["moments"][0] == original:
            tampered["moments"][0] = str(original) + "/1"
    else:
        # Boş moment listesi: input_repr'i kurcala.
        tampered["input_repr"] = str(sealed.get("input_repr", "")) + "_TAMPERED"

    report = verify(tampered)
    return report["result"] == "TAMPERED"


__all__ = [
    "seal",
    "verify",
    "adversarial_control",
    "tamper_test",
    "SEAL_VERSION",
]
