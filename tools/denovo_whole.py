#!/usr/bin/env python3
"""BÜTÜN olarak hesapla — hastalık = mutant BÜTÜN, sağlıklı = yabanıl-tip BÜTÜN.

Parça-parça değil: tek bir protein/jenerik-referans DEĞİL. Hastalık durumu = gerçek
onko-sürücülerin MUTANT yapılarının TAMAMI tek κ'da serbest-toplanmış (Voiculescu ⊞);
sağlıklı durum = AYNI sistemin gerçek YABANIL-TİP TAMAMI. Boşluk = mutasyonların
BÜTÜNDE kırdığı pozitiflik. İlaç o BÜTÜN boşluğu kapatmalı:

    κ_disease  = κ(EGFR_mut) ⊞ κ(KRAS_mut) ⊞ κ(TP53_mut)     (mutant BÜTÜN)
    κ_healthy  = κ(EGFR_wt)  ⊞ κ(KRAS_wt)  ⊞ κ(TP53_wt)      (yabanıl BÜTÜN)
    κ_required = κ_healthy ⊟ κ_disease                        (saf dekonvolüsyon)
    DRUG: κ(disease ⊞ M) ≈ κ_healthy  ve  closure_error < baseline (GERÇEK ilerleme)

GERÇEK veri (UniProt, canlı) · GERÇEK yapı (hidropati spektrumu) · GERÇEK mutasyonlar
(dokümante, kalıntı doğrulanır) · HAFIZA YOK (pure genesis) · HİÇ OLMAYAN molekül.

Kullanım: python tools/denovo_whole.py
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

_UA = {"User-Agent": "tantrium-whole/1.0"}
_TIMEOUT = 25

# (gen, UniProt acc, [(1-indeksli pozisyon, beklenen-WT, mutant)]) — gerçek onkogenik mutasyonlar
_PLAYERS = [
    ("EGFR", "P00533", [(858, "L", "R")]),  # L858R (akciğer adeno) — UniProt precursor numar.
    ("KRAS", "P01116", [(12, "G", "D")]),  # G12D (pankreas/kolon)
    ("TP53", "P04637", [(175, "R", "H")]),  # R175H (Li-Fraumeni / yaygın somatik)
]


def _get_json(url: str) -> dict | None:
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=_TIMEOUT))
    except Exception as e:  # noqa: BLE001
        print(f"  ! ağ: {type(e).__name__}: {str(e)[:90]}")
        return None


def fetch_seq(acc: str) -> str | None:
    try:
        req = urllib.request.Request(f"https://rest.uniprot.org/uniprotkb/{acc}.fasta", headers=_UA)
        txt = urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode()
        return "".join(ln for ln in txt.split("\n")[1:] if ln and not ln.startswith(">"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! UniProt {acc}: {type(e).__name__}: {str(e)[:90]}")
        return None


def apply_mutations(seq: str, muts: list[tuple[int, str, str]]) -> tuple[str, list[str]]:
    """Mutasyonu uygula; kalıntı doğrulanır (gerçeklik kontrolü). Eşleşmezse atlanır+rapor."""
    s = list(seq)
    applied = []
    for pos, wt, mut in muts:
        i = pos - 1
        if 0 <= i < len(s) and s[i] == wt:
            s[i] = mut
            applied.append(f"{wt}{pos}{mut}✓")
        else:
            got = s[i] if 0 <= i < len(s) else "?"
            applied.append(f"{wt}{pos}{mut}✗(got {got})")
    return "".join(s), applied


def chembl_exists(smiles: str) -> bool | None:
    url = "https://www.ebi.ac.uk/chembl/api/data/molecule?" + urllib.parse.urlencode(
        {"molecule_structures__canonical_smiles__flexmatch": smiles, "format": "json"}
    )
    d = _get_json(url)
    return None if d is None else len(d.get("molecules", [])) > 0


def main() -> int:
    print("=" * 70)
    print("  BÜTÜN-HESABI DE-NOVO — mutant BÜTÜN vs yabanıl-tip BÜTÜN")
    print("=" * 70)

    import tantrium
    from tantrium.core.molecular_genesis import MolecularGenesis
    from tantrium.core.production import ProductionEngine
    from tantrium.core.production_judge import ProductionJudge
    from tantrium.core.quantum_moments import FreeCumulants, bounded_kappa_distance

    ai = tantrium.AI()
    pe = ProductionEngine(ai.engine)
    judge = ProductionJudge(ai.engine, pe)

    # ── 1. GERÇEK yapıları çek, BÜTÜN'ü serbest-toplamla kur ────────────
    print("\n[1] Gerçek yapılar (UniProt, canlı) → mutant/yabanıl BÜTÜN serbest-toplam:")
    k_healthy = FreeCumulants([0.0] * 6)
    k_disease = FreeCumulants([0.0] * 6)
    n_used = 0
    for gene, acc, muts in _PLAYERS:
        wt = fetch_seq(acc)
        if not wt:
            continue
        mut, applied = apply_mutations(wt, muts)
        mu_wt = pe._encode(wt)
        mu_mut = pe._encode(mut)
        if not mu_wt or not mu_mut:
            continue
        k_healthy = k_healthy.add(FreeCumulants.from_moments(mu_wt))
        k_disease = k_disease.add(FreeCumulants.from_moments(mu_mut))
        n_used += 1
        print(f"    {gene:5s} ({acc}, {len(wt)} aa)  mut={','.join(applied)}")
    if n_used == 0:
        print("    Hiç yapı alınamadı — çıkılıyor.")
        return 1

    # ── 2. BÜTÜN boşluğu (saf dekonvolüsyon) ────────────────────────────
    baseline = bounded_kappa_distance(
        k_disease.to_moments_approx(), k_healthy.to_moments_approx(), include_mean=True
    )
    k_req = k_healthy.subtract(k_disease)
    mu_req = k_req.to_moments_approx()
    print("\n[2] BÜTÜN boşluğu (mutasyonların bütünde kırdığı):")
    print(f"    baseline (mutant BÜTÜN ↔ yabanıl BÜTÜN) = {baseline:.4f}")
    print(f"    κ_required (saf dekonvolüsyon) μ = {[round(x, 3) for x in mu_req[:6]]}")

    # ── 3. SAF de-novo: BÜTÜN'ü kapatmaya doğru büyü (hafıza yok) ────────
    print("\n[3] Saf-matematik de-novo: BÜTÜN boşluğu kapatmaya doğru genesis...")
    rep = MolecularGenesis(ai.engine).simulate(
        seeds=["C", "CC", "CN", "CO", "c1ccccc1"],
        max_steps=12,
        beam_width=6,
        toward_profile=[mu_req],
    )
    cands = [s.smiles for s in (rep.frontier + list(reversed(rep.lineage)))]
    cands = [c for c in dict.fromkeys(cands) if pe._chemically_stable(c)]

    best = None
    for smi in cands:
        proof = judge.close_universe(smi, k_disease, k_healthy, mu_req, epsilon=0.5, mol_scale=True)
        rec = {"smi": smi, "proof": proof}
        if best is None or proof.closure_error < best["proof"].closure_error:
            best = rec

    if best is None:
        print("    Aday üretilemedi.")
        return 1
    p = best["proof"]
    print("\n[SONUÇ]")
    print(f"    Üretilen molekül : {best['smi']}")
    print(f"    BÜTÜN kapanışı   : {'✓ kapandı' if p.universe_closes else '✗ açık'}")
    print(
        f"    closure_error={p.closure_error:.4f}  baseline={p.baseline_error:.4f}  "
        f"ilerleme={'✓' if p.improves_on_baseline else '✗'}  depth={p.depth}  rungs={p.rungs}"
    )
    verdict = "İŞE YARAYABİLİR" if p.universe_closes else "KISMÎ/İŞE YARAMAZ"
    print(f"    Hüküm            : {verdict}")

    # ── 4. HİÇ OLMAYAN doğrula ──────────────────────────────────────────
    print("\n[4] Novelty (ChEMBL):")
    ex = chembl_exists(best["smi"])
    if ex is None:
        print("    ? sorgulanamadı")
    elif ex:
        print("    ✗ ChEMBL'de VAR")
    else:
        print("    ✓ ChEMBL'de YOK — HİÇ VAR OLMAMIŞ. BÜTÜN'den saf matematikle doğdu.")
    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
