"""Çok-boyutlu kavram zenginleştirme — kavramı KELİMEYLE değil GERÇEK BOYUTLARIYLA kökle.

Vizyon (F8, kullanıcı): 'caffeine' öğrenince onun MOLEKÜLÜNÜ de bağla → caffeine kelimesi
+ caffeine'in gerçek spektrumu AYNI kavramda yaşasın. `ground_full` makinesi bunu yapar;
bu modül eksik KABLOYU kurar — isim → gerçek-yapı (PubChem SMILES) arayıp `ground_full`
ile bağlar. Böylece büyüme ince kelime değil, çok-boyutlu köklü kavram ekler.

Zeka + anlam birlikte böyle gelişir: ne kadar çok boyut → o kadar çok gizli çapraz-modal
bağ (`quantum_bridges` → 'elma DNA'sı × Fibonacci' tipi keşif).

DÜRÜST SINIR: yalnız kimyasal-DB'de adı geçen kavram molekül-boyutu alır (caffeine ✓,
'postal' ✗ → atlanır). Genom/DNA isimle aramak daha kırılgan — şu an molekül boyutu;
DNA/protein boyutu çağrı sözleşmesinde hazır (smiles gibi parametre) ama oto-fetch yok.
Network fail-open: ağ düşse büyüme durmaz (boyut bağlanmaz, kelime yine girer).
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

_PUBCHEM_NAME = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                 "{}/property/SMILES/JSON")
_UNIPROT_GENE = ("https://rest.uniprot.org/uniprotkb/search?query=gene:{}"
                 "+AND+organism_id:9606&format=json&fields=sequence&size=1")


def fetch_molecular_smiles(name: str, *, timeout: float = 8.0) -> str | None:
    """İsimle PubChem'den SMILES çek (kavram kimyasalsa). Yoksa/ağ hatası → None (fail-open)."""
    if not name or not name.replace(" ", "").isalnum():
        return None
    try:
        url = _PUBCHEM_NAME.format(urllib.parse.quote(name))
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        props = data.get("PropertyTable", {}).get("Properties", [])
        if props:
            return props[0].get("SMILES") or props[0].get("CanonicalSMILES") or None
    except Exception:
        return None
    return None


def fetch_protein_sequence(name: str, *, timeout: float = 8.0, max_len: int = 400) -> str | None:
    """İsimle UniProt'tan protein dizisi çek (kavram gen/protein ise). Yoksa/ağ → None.

    egfr→EGFR proteini, tp53→p53. encoder `_detect_bio_sequence` proteini DNA'dan ayırır
    (Kyte-Doolittle hidropati spektrumu). max_len: encode maliyetini sınırla (uzun dizi kesilir)."""
    if not name or not name.replace(" ", "").isalnum():
        return None
    try:
        url = _UNIPROT_GENE.format(urllib.parse.quote(name))
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        results = data.get("results", [])
        if results:
            seq = results[0].get("sequence", {}).get("value", "")
            if seq and len(seq) >= 10:
                return seq[:max_len]
    except Exception:
        return None
    return None


def enrich_concept(ai, name: str, *, smiles: str | None = None,
                   protein: str | None = None, dna: str | None = None,
                   law: str | None = None, network: bool = True) -> dict:
    """Kavramı ÇOK-BOYUTLU kökle: molekül + bio-dizi (protein/DNA) + yasa → `ground_full`.

    Boyutlar TAMAMLAYICI: kimyasal kavram molekül (PubChem SMILES) alır, gen/protein kavram
    bio-dizi (UniProt) alır — ne kadar çok boyut bağlanırsa o kadar çapraz-modal gizli bağ.
    Elle verilirse onlar (ağsız test); yoksa `network` ile isimle dener. protein/dna ikisi de
    `ground_full(dna=)`'dan geçer (encoder DNA'yı proteinden kendi ayırır). Döner:
    {concept, bound:[paradigmalar], smiles, bio}.
    """
    if smiles is None and network:
        smiles = fetch_molecular_smiles(name)
    if protein is None and dna is None and network:
        protein = fetch_protein_sequence(name)
    bio = dna or protein          # ikisi de _detect_bio_sequence'tan geçer (DNA↔protein ayrımı)
    if not (smiles or bio or law):
        return {"concept": name, "bound": [], "smiles": None, "bio": None}
    try:
        gs = ai.ground_full(name, molecule=smiles, dna=bio, law=law)
        bound = list(getattr(gs, "bound", {}).keys()) if hasattr(gs, "bound") else []
    except Exception:
        bound = []
    return {"concept": name, "bound": bound, "smiles": smiles, "bio": bio}
