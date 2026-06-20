#!/usr/bin/env python3
"""Saf-matematik de-novo ilaç üretimi — GERÇEK veri, GERÇEK yapı, HAFIZA YOK.

Tez: ilaç = RH pozitiflik zincirini TERSTEN koşturmak. Hastalık = bozulmuş pozitiflik;
ilaç = onu sağlıklıya taşıyan serbest-dekonvolüsyon molekülü. Bu script onu UÇTAN UCA,
GERÇEK veriyle ve HİÇBİR genelleme/hafıza-aktarımı olmadan gösterir:

  1. GERÇEK VERİ (canlı çek):
       • ChEMBL  → hastalık sürücüsü hedefin GERÇEK kimliği (target_chembl_id)
       • UniProt → o hedefin GERÇEK protein dizisi (birincil yapı, 1000+ kalıntı)
  2. GERÇEK YAPI ile gir: dizi → encode_protein (Kyte-Doolittle hidropati → Wiener–Khinchin
       spektrumu) → κ_disease. "Harf" değil, GERÇEK biyofiziksel ölçü (CLAUDE.md F24 yasası).
  3. SAF MATEMATİK üret: κ_required = κ_healthy ⊟ κ_disease (serbest dekonvolüsyon);
       produce(pure_denovo=True) → YALNIZ genesis + reconstruction (kütüphane/scaffold/morph/
       bilinen-ligand KAPALI). Molekül CH/CC primitiflerinden Sturm-geçitli büyür.
  4. HİÇ OLMAYAN doğrula: üretilen SMILES'ı ChEMBL'de ARA — bulunmazsa "hiç var olmamış".

Çıktı: üretilen molekül + evren-kapanışı sertifikası + novelty hükmü. Bilinen ilaç GERİ
ÇEKİLMEZ; üretilen manifolda enjekte EDİLMEZ (öğrenme geri-sızması yok).

Kullanım:
    python tools/denovo_from_chembl.py                 # EGFR (P00533) varsayılan
    python tools/denovo_from_chembl.py BRAF P15056     # başka hedef + UniProt acc
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

_UA = {"User-Agent": "tantrium-denovo/1.0"}
_TIMEOUT = 25


def _get_json(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=_UA)
        return json.load(urllib.request.urlopen(req, timeout=_TIMEOUT))
    except Exception as e:  # noqa: BLE001
        print(f"  ! ağ hatası: {type(e).__name__}: {str(e)[:100]}")
        return None


def fetch_chembl_target(name: str) -> tuple[str, str] | None:
    """ChEMBL'den GERÇEK hedef kimliği (canlı)."""
    url = (
        "https://www.ebi.ac.uk/chembl/api/data/target/search?"
        + urllib.parse.urlencode({"q": name, "format": "json", "limit": 1})
    )
    d = _get_json(url)
    if d and d.get("targets"):
        t = d["targets"][0]
        return t["target_chembl_id"], t.get("pref_name", name)
    return None


def fetch_uniprot_sequence(acc: str) -> str | None:
    """UniProt'tan GERÇEK protein dizisi (birincil yapı, canlı)."""
    try:
        req = urllib.request.Request(
            f"https://rest.uniprot.org/uniprotkb/{acc}.fasta", headers=_UA
        )
        txt = urllib.request.urlopen(req, timeout=_TIMEOUT).read().decode()
        return "".join(line for line in txt.split("\n")[1:] if line and not line.startswith(">"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! UniProt hatası: {type(e).__name__}: {str(e)[:100]}")
        return None


def chembl_smiles_exists(smiles: str) -> bool | None:
    """Üretilen SMILES ChEMBL'de VAR MI? (novelty kanıtı). None = sorgulanamadı."""
    url = (
        "https://www.ebi.ac.uk/chembl/api/data/molecule?"
        + urllib.parse.urlencode(
            {"molecule_structures__canonical_smiles__flexmatch": smiles, "format": "json"}
        )
    )
    d = _get_json(url)
    if d is None:
        return None
    return len(d.get("molecules", [])) > 0


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "EGFR"
    acc = sys.argv[2] if len(sys.argv) > 2 else "P00533"

    print("=" * 70)
    print(f"  SAF-MATEMATİK DE-NOVO ÜRETİM — hedef: {name} (UniProt {acc})")
    print("=" * 70)

    # ── 1. GERÇEK VERİ ──────────────────────────────────────────────────
    print("\n[1] GERÇEK veri çekiliyor (canlı)...")
    tgt = fetch_chembl_target(name)
    if tgt:
        print(f"    ChEMBL hedef : {tgt[0]}  ({tgt[1]})")
    seq = fetch_uniprot_sequence(acc)
    if not seq:
        print("    UniProt dizisi alınamadı — çıkılıyor (gerçek yapı şart).")
        return 1
    print(f"    UniProt dizi : {len(seq)} kalıntı  [{seq[:36]}...]")

    # ── 2 & 3. GERÇEK YAPI ile gir → SAF MATEMATİK üret ─────────────────
    print("\n[2] Gerçek yapı encode ediliyor (hidropati → spektrum → κ_disease)...")
    print("[3] Saf-matematik de-novo üretim (kütüphane/scaffold/morph KAPALI)...")
    import tantrium
    from tantrium.core.production import ProductionEngine

    ai = tantrium.AI()
    pe = ProductionEngine(ai.engine)
    # Hastalık bulgusu = hedefin GERÇEK dizisi (aşırı-aktif sürücü). Liste-of-str → findings yolu.
    cert = pe.produce(
        [seq],
        max_steps=10,
        beam_width=5,
        combination=False,
        inject=False,
        pure_denovo=True,
    )

    smi = cert.designed_smiles
    print("\n[SONUÇ]")
    print(f"    Üretilen molekül : {smi}")
    print(f"    Atom sayısı      : {cert.n_atoms}")
    print(f"    Hüküm            : {cert.verdict}")
    if cert.closure and cert.closure.applicable:
        c = cert.closure
        print(
            f"    Evren kapanışı   : {'✓' if c.universe_closes else '✗'}  "
            f"closure_error={c.closure_error:.4f}  baseline={c.baseline_error:.4f}  "
            f"ilerleme={'✓' if c.improves_on_baseline else '✗'}"
        )
        print(f"    Sturm yolu (geçerli ölçü): {'✓' if c.sturm_ok else '✗'}  depth={c.depth}")
    print(f"    Sturm path ok    : {cert.sturm_path_ok}  pivot_min={cert.pivot_min:+.4f}")

    # ── 4. HİÇ OLMAYAN doğrula ──────────────────────────────────────────
    print("\n[4] Novelty: üretilen molekül ChEMBL'de var mı?")
    if not smi:
        print("    (molekül üretilemedi)")
        return 1
    exists = chembl_smiles_exists(smi)
    if exists is None:
        print("    ? ChEMBL sorgulanamadı (ağ) — novelty doğrulanamadı.")
    elif exists:
        print("    ✗ ChEMBL'de VAR — bu yapı zaten biliniyor (hafıza sızıntısı? incele).")
    else:
        print("    ✓ ChEMBL'de YOK — HİÇ VAR OLMAMIŞ bir molekül. Saf matematikten doğdu.")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
