#!/usr/bin/env python3
"""AŞİL TOPUĞU saldırısı — global boşluk DEĞİL, hastalığın EN ZAYIF eksenine direkt vuruş.

Doğru mimari (kullanıcı): tüm RH pozitiflik kriterlerini (ALEPH/DALET/HE/ZAYIN/TAU
paradigma marjinleri) tüm gerçek veriden hesapla, hastalık-BÜTÜN ile sağlıklı-BÜTÜN'ü
KRİTİK ÇİZGİDE karşılaştır, hastalığın SAĞLIKLIDAN EN ÇOK SAPTIĞI ekseni (= aşil topuğu)
bul, ve füzyon (hastalık ⊞ M) o ekseni kritik çizgiye geri taşıyan molekülü tasarla.

Neden global kapanış YANLIŞTI: closure_error tüm eksenleri ORTALAR. Nokta-mutasyonu TEK
ekseni keskin kırar (ör. ZAYIN/Schur yapısal tutarlılık) ama global mesafe ~0 kalır
(bütün-protein 0.0086) → sinyal ortalamada silinir. Aşil topuğu o tek zayıf ekseni
İZOLE eder; saldırı oraya odaklanır. crypto.achilles(savunma) ile AYNI GIMEL makinesi.

GERÇEK veri (UniProt canlı) · GERÇEK mutasyonlar (doğrulanır) · HAFIZA YOK · HİÇ OLMAYAN.
"""

from __future__ import annotations

import urllib.request

_UA = {"User-Agent": "tantrium-achilles/1.0"}
_TIMEOUT = 25
_AXES = ("ALEPH", "DALET", "HE", "ZAYIN", "TAU")

_PLAYERS = [
    ("EGFR", "P00533", [(858, "L", "R")]),
    ("KRAS", "P01116", [(12, "G", "D")]),
    ("TP53", "P04637", [(175, "R", "H")]),
]


def fetch_seq(acc: str) -> str | None:
    try:
        req = urllib.request.Request(f"https://rest.uniprot.org/uniprotkb/{acc}.fasta", headers=_UA)
        txt = urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode()
        return "".join(ln for ln in txt.split("\n")[1:] if ln and not ln.startswith(">"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! UniProt {acc}: {type(e).__name__}")
        return None


def apply_mut(seq: str, muts) -> tuple[str, list[str]]:
    s, applied = list(seq), []
    for pos, wt, mut in muts:
        i = pos - 1
        if 0 <= i < len(s) and s[i] == wt:
            s[i] = mut
            applied.append(f"{wt}{pos}{mut}✓")
        else:
            applied.append(f"{wt}{pos}{mut}✗")
    return "".join(s), applied


def main() -> int:
    print("=" * 72)
    print("  AŞİL TOPUĞU SALDIRISI — hastalığın en zayıf RH eksenine direkt vuruş")
    print("=" * 72)

    import tantrium
    from tantrium.core.molecular_genesis import MolecularGenesis
    from tantrium.core.production import ProductionEngine
    from tantrium.core.quantum_moments import FreeCumulants

    ai = tantrium.AI()
    pe = ProductionEngine(ai.engine)
    enc = ai.engine.encoder

    def margins(k: FreeCumulants) -> dict:
        """κ → moment → pipeline GIMEL paradigm_margins (her eksenin pozitiflik marjı)."""
        mu = k.to_moments_approx()
        st = enc.encode([float(x) for x in mu]).structure
        return {a: float(st.get("paradigm_margins", {}).get(a, 0.0)) for a in _AXES}

    # ── 1. BÜTÜN'ü kur (gerçek mutant vs yabanıl) ───────────────────────
    print("\n[1] Gerçek BÜTÜN (UniProt canlı, mutant vs yabanıl-tip):")
    kH = FreeCumulants([0.0] * 6)
    kD = FreeCumulants([0.0] * 6)
    used = 0
    for gene, acc, muts in _PLAYERS:
        wt = fetch_seq(acc)
        if not wt:
            continue
        mut, applied = apply_mut(wt, muts)
        muw, mum = pe._encode(wt), pe._encode(mut)
        if not muw or not mum:
            continue
        kH = kH.add(FreeCumulants.from_moments(muw))
        kD = kD.add(FreeCumulants.from_moments(mum))
        used += 1
        print(f"    {gene:5s} {acc} ({len(wt)} aa)  {','.join(applied)}")
    if used == 0:
        print("    veri yok — çık")
        return 1

    # ── 2. AŞİL TOPUĞU: hastalığın sağlıklıdan EN ÇOK saptığı eksen ──────
    mH, mD = margins(kH), margins(kD)
    dev = {a: abs(mD[a] - mH[a]) for a in _AXES}
    achilles = max(_AXES, key=lambda a: dev[a])
    print("\n[2] Kritik-çizgi eksen marjinleri (paradigma pozitifliği):")
    for a in _AXES:
        flag = "  ← AŞİL" if a == achilles else ""
        print(f"    {a:6s} sağlıklı={mH[a]:+.5f}  hastalık={mD[a]:+.5f}  sapma={dev[a]:.5f}{flag}")
    print(f"\n    AŞİL TOPUĞU = {achilles}  (hastalığın en kırık ekseni, sapma={dev[achilles]:.5f})")

    # ── 3. SALDIRI: füzyon o ekseni kritik çizgiye taşıyan de-novo molekül ─
    print(f"\n[3] Saf de-novo: füzyon (hastalık ⊞ M) {achilles} eksenini sağlıklıya taşısın...")
    rep = MolecularGenesis(ai.engine).simulate(
        seeds=["C", "CC", "CN", "CO", "CCO", "c1ccccc1", "C1CCNCC1"],
        max_steps=12,
        beam_width=6,
        toward_profile=[kH.subtract(kD).to_moments_approx()],
    )
    cands = [s.smiles for s in (rep.frontier + list(reversed(rep.lineage)))]
    cands = [c for c in dict.fromkeys(cands) if pe._chemically_stable(c)]

    target = mH[achilles]  # kritik-çizgi hedefi (sağlıklı marj)
    base_gap = abs(mD[achilles] - target)
    best = None
    for smi in cands:
        muM = pe._encode(smi)
        if not muM:
            continue
        fused = kD.add(FreeCumulants.from_moments(muM))
        mF = margins(fused)
        gap_after = abs(mF[achilles] - target)
        repair = base_gap - gap_after  # >0 = aşil ekseni sağlıklıya YAKLAŞTI (saldırı tuttu)
        # yeni aşil yaratmasın: füzyonun en kötü ekseni hastalıktan kötü olmamalı
        worsened = max(abs(mF[a] - mH[a]) for a in _AXES) > max(dev.values()) + 1e-6
        rec = {"smi": smi, "repair": repair, "gap_after": gap_after, "mF": mF, "worsened": worsened}
        if best is None or (not worsened and repair > best["repair"]):
            best = rec

    if best is None:
        print("    aday yok")
        return 1

    b = best
    hit = b["repair"] > 0 and not b["worsened"]
    print("\n[SONUÇ]")
    print(f"    Üretilen molekül : {b['smi']}")
    print(f"    AŞİL ekseni {achilles}:  hastalık={mD[achilles]:+.5f} → füzyon={b['mF'][achilles]:+.5f}"
          f"  (hedef sağlıklı={target:+.5f})")
    print(f"    Onarım (sapma azalması): {b['repair']:+.5f}  "
          f"({base_gap:.5f} → {b['gap_after']:.5f})")
    print(f"    Yeni aşil yarattı mı: {'EVET (kötü)' if b['worsened'] else 'HAYIR'}")
    print(f"    HÜKÜM: {'✓ SALDIRI TUTTU — aşil ekseni kritik çizgiye taşındı' if hit else '✗ tutmadı'}")
    print("\n" + "=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
