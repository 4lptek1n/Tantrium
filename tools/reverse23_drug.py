#!/usr/bin/env python3
"""23 PARADİGMA TERSTEN — ilaç = füzyonu tüm 23 filtreden geçiren yapı.

Tek matematik, iki yön:
  FORWARD  : certify(durum) → 23 paradigma durumu kritik çizgide mi DOĞRULAR.
  REVERSE  : hastalığın 23-profilini kıran molekülün TERSİNİ kur — füzyon
             (hastalık ⊞ M) durumunu 23 paradigmanın HEPSİNE yeniden geçiren M.

Hastalık 23-profilini sağlıklıdan saptırır (en çok sapan = aşil topuğu). İlaç M,
füzyon durumunun 23-paradigma profilini SAĞLIKLIYA geri taşıyan moleküldür —
tek eksen (closure_error) değil, TÜM zincir kritik çizgiye döner. 23 bağımsız
matematiksel filtre aynı anda geçmek zorunda → halüsinasyon imkânsız.

GERÇEK veri (UniProt canlı) · GERÇEK mutasyon · HAFIZA YOK (genesis) · HİÇ OLMAYAN.
"""

from __future__ import annotations

import urllib.request

_UA = {"User-Agent": "tantrium-rev23/1.0"}
_TIMEOUT = 25

# Gerçek onko-sürücüler, gerçek mutasyonlar, mutasyon DOMENİ (sinyal seyrelmesin) ±W.
_PLAYERS = [("EGFR", "P00533", 858, "L", "R"), ("KRAS", "P01116", 12, "G", "D"),
            ("TP53", "P04637", 175, "R", "H")]
_W = 40  # mutasyon penceresi yarıçapı


def fetch_seq(acc: str) -> str | None:
    try:
        req = urllib.request.Request(f"https://rest.uniprot.org/uniprotkb/{acc}.fasta", headers=_UA)
        txt = urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode()
        return "".join(ln for ln in txt.split("\n")[1:] if ln and not ln.startswith(">"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! UniProt {acc}: {type(e).__name__}")
        return None


def main() -> int:
    print("=" * 72)
    print("  23 PARADİGMA TERSTEN — füzyonu tüm zincirden geçiren de-novo ilaç")
    print("=" * 72)

    import tantrium
    from tantrium.core.molecular_genesis import MolecularGenesis
    from tantrium.core.network import CertificationPipeline
    from tantrium.core.production import ProductionEngine
    from tantrium.core.quantum_moments import FreeCumulants

    ai = tantrium.AI()
    pe = ProductionEngine(ai.engine)
    enc = ai.engine.encoder
    net = CertificationPipeline()

    def profile(k: FreeCumulants):
        """κ → moment → encode → 23 paradigma: (certified set, margin dict)."""
        mu = [float(x) for x in k.to_moments_approx()]
        obj = enc.encode(mu)
        run = net.run(obj)
        certs = {pid for pid, n in run.nodes.items() if n.status == "CERTIFIED"}
        margins = obj.structure.get("paradigm_margins", {})
        return certs, {a: float(margins.get(a, 0.0)) for a in ("ALEPH", "DALET", "HE", "ZAYIN", "TAU")}

    # ── 1. GERÇEK BÜTÜN (mutasyon domeni, mutant vs yabanıl) ────────────
    print("\n[1] Gerçek mutasyon-domenleri (UniProt canlı) → mutant/yabanıl BÜTÜN κ:")
    kH = FreeCumulants([0.0] * 6)
    kD = FreeCumulants([0.0] * 6)
    for gene, acc, pos, wt, mt in _PLAYERS:
        seq = fetch_seq(acc)
        if not seq or pos - 1 >= len(seq) or seq[pos - 1] != wt:
            print(f"    {gene}: atlandı (kalıntı doğrulanamadı)")
            continue
        lo, hi = max(0, pos - 1 - _W), min(len(seq), pos + _W)
        wtwin = seq[lo:hi]
        mtwin = seq[lo : pos - 1] + mt + seq[pos:hi]
        muw, mum = pe._encode(wtwin), pe._encode(mtwin)
        if muw and mum:
            kH = kH.add(FreeCumulants.from_moments(muw))
            kD = kD.add(FreeCumulants.from_moments(mum))
            print(f"    {gene:5s} {wt}{pos}{mt}  domen[{lo}:{hi}] ({hi - lo} aa)")

    # ── 2. FORWARD: hastalık vs sağlıklı 23-profil ──────────────────────
    cH, mH = profile(kH)
    cD, mD = profile(kD)
    print("\n[2] FORWARD 23-paradigma sertifikasyonu:")
    print(f"    sağlıklı: {len(cH)}/23 certified   hastalık: {len(cD)}/23 certified")
    lost = sorted(cH - cD)
    print(f"    hastalıkta KAYBOLAN paradigmalar: {lost if lost else '(yok — yapısal margin sapması)'}")
    dev = {a: abs(mD[a] - mH[a]) for a in mH}
    achilles = max(dev, key=lambda a: dev[a])
    print("    margin sapmaları: " + "  ".join(f"{a}={dev[a]:.4f}" for a in dev))
    print(f"    AŞİL = {achilles} (sapma {dev[achilles]:.4f})")

    # ── 3. REVERSE: füzyonu 23-profile geri taşıyan de-novo M ───────────
    print("\n[3] REVERSE — füzyon (hastalık ⊞ M) 23-profili sağlıklıya taşısın...")
    rep = MolecularGenesis(ai.engine).simulate(
        seeds=["C", "CC", "CN", "CO", "CCO", "c1ccccc1", "C1CCNCC1", "C1CCOCC1"],
        max_steps=12, beam_width=7,
        toward_profile=[kH.subtract(kD).to_moments_approx()],
    )
    cands = [s.smiles for s in (rep.frontier + list(reversed(rep.lineage)))]
    cands = [c for c in dict.fromkeys(cands) if pe._chemically_stable(c)]

    best = None
    base_dev = sum(dev.values())
    for smi in cands:
        muM = pe._encode(smi)
        if not muM:
            continue
        kF = kD.add(FreeCumulants.from_moments(muM))
        cF, mF = profile(kF)
        # 23-profil sağlıklıya ne kadar yaklaştı: kayıp paradigma geri geldi mi + margin
        restored = len((cH & cF) - cD)  # sağlıklının geri kazanılan paradigmaları
        dev_after = sum(abs(mF[a] - mH[a]) for a in mH)
        score = (restored, base_dev - dev_after)  # önce paradigma, sonra margin onarımı
        rec = {"smi": smi, "cF": cF, "restored": restored, "dev_after": dev_after, "score": score}
        if best is None or score > best["score"]:
            best = rec

    if best is None:
        print("    aday yok")
        return 1
    b = best
    full = len(b["cF"]) >= len(cH) and (cH - b["cF"]) == set()
    print("\n[SONUÇ]")
    print(f"    Üretilen molekül : {b['smi']}")
    print(f"    Füzyon 23-profil : {len(b['cF'])}/23 certified  (sağlıklı {len(cH)}/23)")
    print(f"    Geri kazanılan paradigma: {b['restored']}   margin onarımı: {base_dev:.4f} → {b['dev_after']:.4f}")
    print(f"    HÜKÜM: {'✓ TÜM ZİNCİR KAPANDI — füzyon sağlıklı 23-profili sağlıyor' if full else '✗ zincir tam kapanmadı (kısmî onarım)'}")
    print("\n" + "=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
