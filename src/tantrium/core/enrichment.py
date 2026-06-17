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


def enrich_concept(ai, name: str, *, smiles: str | None = None,
                   dna: str | None = None, law: str | None = None,
                   network: bool = True) -> dict:
    """Kavramı çok-boyutlu kökle: molekül (+verilmişse DNA/yasa) boyutunu `ground_full`'le bağla.

    `smiles`/`dna`/`law` verilirse onlar kullanılır (deterministik, ağsız test edilebilir);
    `smiles` yok + `network` ise PubChem'den isimle dener. Döner: {concept, bound:[paradigmalar], smiles}.
    """
    if smiles is None and network:
        smiles = fetch_molecular_smiles(name)
    if not (smiles or dna or law):
        return {"concept": name, "bound": [], "smiles": None}
    try:
        gs = ai.ground_full(name, molecule=smiles, dna=dna, law=law)
        bound = list(getattr(gs, "bound", {}).keys()) if hasattr(gs, "bound") else []
    except Exception:
        bound = []
    return {"concept": name, "bound": bound, "smiles": smiles}
