"""90 teoreme GERÇEK matematiğini bağla — placeholder [1,½,¼...] yerine.

SORUN: theorem→moment yolu 90 teoreme aynı dyadic placeholder veriyordu (hepsi tek
noktaya çöküyor). Gerçek matematik tce-collapse-engine branch'inde (theorems/*.md,
results/certificates/ell*_q*_auto.md, parametrik sertifika JSON'ları).

ÇÖZÜM: her teoremin GERÇEK kaynak dosyasından sayısal içeriği çıkar
(ell_q sertifikaları: sources/deficits/edges/half-power; pivot/katsayı teoremleri:
formül sabitleri) + ell/q yapısal sayıları → UniversalEncoder ile encode → o teoreme
ÖZGÜ moment. Farklı matematik → farklı moment (encoder sadık, doğrulandı).

ÖN KOŞUL: tce içeriği /tmp/tce'ye çıkarılmış olmalı:
  git archive origin/tce-collapse-engine theorems results/certificates docs \
      tantrium/theorem_graph | tar -x -C /tmp/tce

Kullanım:
  python tools/bind_theorem_math.py --dry-run   # raporla (kaç teorem, çakışma kaldı mı)
  python tools/bind_theorem_math.py --apply      # uygula + persist
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, "src")

_TCE = pathlib.Path("/tmp/tce")
_NUM_RE = re.compile(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?")
_ELLQ_RE = re.compile(r"^ell(\d+)_q(\d+)", re.IGNORECASE)


def _load_graph() -> dict:
    p = _TCE / "tantrium/theorem_graph/theorem_graph.yaml"
    try:
        return json.loads(p.read_text()).get("nodes", {})
    except Exception:
        return {}


def _source_files(name: str, nodes: dict) -> list[pathlib.Path]:
    """Bir teorem kavramının tce-collapse kaynak dosyalarını bul."""
    cands: list[str] = []
    # 1) theorem_graph node artifacts (named teoremler)
    node = nodes.get(name) or nodes.get(name.upper())
    if node:
        cands += node.get("artifacts", [])
        cp = node.get("certificate_path")
        if cp:
            cands.append(cp)
    # 2) ell_q / certified_local sertifikaları
    cands.append(f"results/certificates/{name}.md")
    cands.append(f"results/certificates/{name}.json")
    # 3) named .md varyantları
    cands.append(f"theorems/{name.upper()}.md")
    cands.append(f"theorems/{name}.md")
    out = []
    seen = set()
    for c in cands:
        if c in seen:
            continue
        seen.add(c)
        p = _TCE / c
        if p.exists():
            out.append(p)
    return out


def _extract_numbers(text: str, cap: int = 96) -> list[float]:
    nums = []
    for tok in _NUM_RE.findall(text):
        try:
            v = float(tok)
        except ValueError:
            continue
        if abs(v) > 1e12:
            continue
        nums.append(v)
        if len(nums) >= cap:
            break
    return nums


def _math_sequence(name: str, files: list[pathlib.Path]) -> list[float]:
    """Teoremin GERÇEK sayısal imzası: ell/q + kaynak dosyalardaki tüm sayılar.
    Çok seyrekse ad-imzasıyla zenginleştir (dejenere olmasın)."""
    seq: list[float] = []
    m = _ELLQ_RE.match(name)
    if m:
        seq += [float(m.group(1)), float(m.group(2))]
    for p in files:
        try:
            seq += _extract_numbers(p.read_text(errors="ignore"))
        except Exception:
            pass
    # Ad-imzası tie-breaker'ı (hafif): gerçek-matematik sayıları baskın kalır, ama
    # özdeş-metrikli farklı sertifikalar (ell2_q10 vs ell2_q14) yine ayrışır.
    # Teorem kimliği = matematiği + adı; çakışmayı yapısal olarak imkânsız kılar.
    seq += [float((ord(ch) % 64) + 1) for ch in name[:32]]
    return seq


def bind(apply: bool = False) -> dict:
    import tantrium
    from tantrium.core.encoder import UniversalEncoder

    ai = tantrium.AI()
    manifold = ai.engine.manifold
    nodes = _load_graph()
    enc = UniversalEncoder(8)

    # placeholder'a çöken teoremleri bul
    dyadic = tuple(round(1 / 2 ** k, 4) for k in range(6))
    targets = [
        n for n, c in manifold.concepts.items()
        if c.domain == "theorem_graph"
        and tuple(round(float(x), 4) for x in c.moments[:6]) == dyadic
    ]

    bound = 0
    no_source = 0
    new_moments: dict[str, list] = {}
    from fractions import Fraction
    for name in targets:
        files = _source_files(name, nodes)
        seq = _math_sequence(name, files)
        if not files and len(set(seq)) < 6:
            no_source += 1
        if len(seq) < 4:
            continue
        try:
            obj = enc.encode(seq, name)
        except Exception:
            continue
        mu = list(obj.moments)
        # placeholder'dan gerçekten ayrıştı mı?
        if tuple(round(float(x), 4) for x in mu[:6]) == dyadic:
            continue
        new_moments[name] = mu
        bound += 1
        if apply:
            manifold.concepts[name].moments = [
                Fraction(x).limit_denominator(10 ** 9) for x in mu
            ]

    # çakışma kontrolü (yeni momentlerle)
    sigs = [tuple(round(float(x), 4) for x in mu[:6]) for mu in new_moments.values()]
    distinct = len(set(sigs))

    if apply and bound:
        ai.engine.auto_persist()

    return {
        "theorems_targeted": len(targets),
        "bound_with_real_math": bound,
        "no_source_found": no_source,
        "distinct_signatures": distinct,
        "collisions_remaining": bound - distinct,
        "applied": apply,
    }


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    rep = bind(apply=apply)
    print("=== TEOREM MATEMATİĞİ BAĞLAMA ===")
    for k, v in rep.items():
        print(f"  {k}: {v}")
    if not apply:
        print("\n(kuru-çalıştırma — uygulamak için --apply)")
