"""Çok-boyutlu kavram zenginleştirme — kavramı KELİMEYLE değil tüm GERÇEK BOYUTLARIYLA kökle.

Vizyon (F8, kullanıcı): 'caffeine'/'egfr'/'elma' öğrenince onun MOLEKÜLÜNÜ, PROTEİNİNİ,
DNA'sını, FİZİKSEL imzasını da bağla → her boyut AYNI kavramda gerçek spektrumuyla yaşasın.
Ne kadar çok BAĞIMSIZ boyut → o kadar çapraz-modal gizli bağ (`quantum_bridges` → görmediğimiz
bağlar) → o kadar genelleşen, kendi kendini genişleten zeka.

MİMARİ — genişletilebilir BOYUT-REGİSTRY (`_DIMENSIONS`): her boyut = (anahtar, paradigma,
isim→değer fetcher, bağlama). Yeni boyut eklemek = registry'ye bir `Dimension`. Tip-farkında:
kimyasal kavram molekül+özellik alır, gen/protein bio-dizi alır, ilgisiz (postal) hiçbiri (None
→ atlanır). Network fail-open, idempotent (zaten-bağlı atlanır).

DÜRÜST SINIR (canlı doğrulanmış kaynaklar): molekül(PubChem) · protein(UniProt) ·
DNA-nükleotid(NCBI) · fiziksel-özellik(PubChem) ÇALIŞIYOR. Yasa-boyutu(OEIS) bu ortamda 403;
3D-geometri RDKit ister (yok). Onlar registry'de hazır-kablo ama oto-fetch DEVRE-DIŞI (eklenince
açılır). İsim-eşleşme gevşek olabilir (gen adı ≈ ilaç adı) — bio (UniProt/NCBI) kesin, molekül
gevşek; quality_gate isim-doğrulamayı buraya ekleyebilir.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

_PUBCHEM_NAME = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                 "{}/property/SMILES/JSON")
_PUBCHEM_PROPS = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                  "{}/property/MolecularWeight,XLogP,TPSA,Complexity/JSON")
_UNIPROT_GENE = ("https://rest.uniprot.org/uniprotkb/search?query=gene:{}"
                 "+AND+organism_id:9606&format=json&fields=sequence&size=1")
_NCBI_SEARCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nuccore"
                "&term={}[gene]+AND+human[orgn]+AND+mRNA[filter]&retmax=1&retmode=json")
_NCBI_FETCH = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore"
               "&id={}&rettype=fasta&retmode=text")


def _valid_name(name: str) -> bool:
    return bool(name) and name.replace(" ", "").isalnum()


def _get_json(url: str, timeout: float) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _get_text(url: str, timeout: float) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


# ─── Fetcher'lar (hepsi canlı-doğrulanmış; isim→gerçek boyut) ──────────────────

def fetch_molecular_smiles(name: str, *, timeout: float = 8.0) -> str | None:
    """İsimle PubChem SMILES (kavram kimyasalsa). Yoksa/ağ → None (fail-open)."""
    if not _valid_name(name):
        return None
    data = _get_json(_PUBCHEM_NAME.format(urllib.parse.quote(name)), timeout)
    if data:
        props = data.get("PropertyTable", {}).get("Properties", [])
        if props:
            return props[0].get("SMILES") or props[0].get("CanonicalSMILES") or None
    return None


def fetch_protein_sequence(name: str, *, timeout: float = 8.0, max_len: int = 400) -> str | None:
    """İsimle UniProt protein dizisi (gen/protein kavram). egfr→EGFR proteini."""
    if not _valid_name(name):
        return None
    data = _get_json(_UNIPROT_GENE.format(urllib.parse.quote(name)), timeout)
    if data:
        results = data.get("results", [])
        if results:
            seq = results[0].get("sequence", {}).get("value", "")
            if seq and len(seq) >= 10:
                return seq[:max_len]
    return None


def fetch_dna_sequence(name: str, *, timeout: float = 10.0, max_len: int = 400) -> str | None:
    """İsimle NCBI nükleotid (gen → mRNA/DNA dizisi). egfr→gerçek EGFR mRNA."""
    if not _valid_name(name):
        return None
    es = _get_json(_NCBI_SEARCH.format(urllib.parse.quote(name)), timeout)
    if not es:
        return None
    ids = es.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return None
    fa = _get_text(_NCBI_FETCH.format(ids[0]), timeout)
    if fa and fa.startswith(">"):
        seq = "".join(fa.split("\n")[1:]).strip()
        # yalnız nükleotid alfabesi (FASTA başlığı/açıklama sızmasın)
        seq = "".join(c for c in seq.upper() if c in "ACGTN")
        if len(seq) >= 10:
            return seq[:max_len]
    return None


def fetch_physical_properties(name: str, *, timeout: float = 8.0) -> list[float] | None:
    """İsimle PubChem fiziksel özellik vektörü (MW/XLogP/TPSA/Complexity) — yapıdan BAĞIMSIZ kanal."""
    if not _valid_name(name):
        return None
    data = _get_json(_PUBCHEM_PROPS.format(urllib.parse.quote(name)), timeout)
    if data:
        props = data.get("PropertyTable", {}).get("Properties", [{}])[0]
        vec = []
        for k in ("MolecularWeight", "XLogP", "TPSA", "Complexity"):
            v = props.get(k)
            if v is not None:
                try:
                    vec.append(float(v))
                except (ValueError, TypeError):
                    pass
        if len(vec) >= 2:
            return vec
    return None


# ─── Bağlama (her boyut → percept + TAU kenarı, bind_percept üzerinden) ────────

def _bind_bio(ai, concept: str, seq: str, key: str) -> None:
    """Bio-dizi (protein/DNA) bağla — encoder _detect_bio_sequence DNA↔protein'i kendi ayırır."""
    ai.bind_percept(concept, seq, modality="smiles", paradigm="HAS_DNA",
                    name=f"⟨percept:{concept}:{key}⟩")


def _bind_molecule(ai, concept: str, smiles: str, key: str) -> None:
    ai.bind_percept(concept, smiles, modality="smiles", paradigm="HAS_COMPOUND",
                    name=f"⟨percept:{concept}:molecule⟩")


def _bind_properties(ai, concept: str, vec: list[float], key: str) -> None:
    """Fiziksel özellik vektörü → PSD geometri matrisi (dış-çarpım) → HAS_GEOMETRY."""
    import numpy as np
    v = np.array([float(x) for x in vec], dtype=float)
    nrm = float(np.linalg.norm(v)) or 1.0
    v = v / nrm
    mat = np.outer(v, v)                      # rank-1 PSD → encode_matrix momentleri
    ai.bind_percept(concept, mat, modality="matrix", paradigm="HAS_GEOMETRY",
                    name=f"⟨percept:{concept}:properties⟩")


# ─── Genişletilebilir boyut REGİSTRY'si ───────────────────────────────────────

@dataclass(frozen=True)
class Dimension:
    key: str                                  # "molecule" / "protein" / "dna" / "properties"
    paradigm: str                             # HAS_COMPOUND / HAS_DNA / HAS_GEOMETRY
    fetch: Callable[[str], Any]               # isim → gerçek değer veya None
    bind: Callable[[Any, str, Any, str], None]  # (ai, concept, value, key) → bağla


# Sıra: kesin-eşleşenler (bio) önce, gevşek (molekül) sonra. Yeni boyut = bir satır.
_DIMENSIONS: list[Dimension] = [
    Dimension("protein", "HAS_DNA", fetch_protein_sequence, _bind_bio),
    Dimension("dna", "HAS_DNA", fetch_dna_sequence, _bind_bio),
    Dimension("molecule", "HAS_COMPOUND", fetch_molecular_smiles, _bind_molecule),
    Dimension("properties", "HAS_GEOMETRY", fetch_physical_properties, _bind_properties),
]

# Elle-override anahtarları (ağsız test / kullanıcı verisi) → boyut anahtarı eşlemesi.
_MANUAL_ALIASES = {"smiles": "molecule", "protein": "protein", "dna": "dna",
                   "properties": "properties"}


def enrich_concept(ai, name: str, *, network: bool = True, dims: list[str] | None = None,
                   **manual) -> dict:
    """Kavramı TÜM uygulanabilir boyutlarda kökle (registry). Tip-farkında, fail-open, idempotent.

    `manual` (smiles=/protein=/dna=/properties=) elle değer verir (ağsız test); yoksa `network`
    ile fetcher dener. `dims` verilirse yalnız o boyutlar denenir. Döner:
    {concept, bound:[paradigmalar], dimensions:[anahtarlar], values:{anahtar→özet}}.
    """
    manual_by_key = {_MANUAL_ALIASES[k]: v for k, v in manual.items()
                     if k in _MANUAL_ALIASES and v is not None}
    bound: list[str] = []
    dims_bound: list[str] = []
    values: dict[str, str] = {}
    seen_paradigms: set[str] = set()
    for dim in _DIMENSIONS:
        if dims is not None and dim.key not in dims:
            continue
        val = manual_by_key.get(dim.key)
        if val is None and network:
            try:
                val = dim.fetch(name)
            except Exception:
                val = None
        if val is None or (isinstance(val, str) and not val):
            continue
        try:
            dim.bind(ai, name, val, dim.key)
        except Exception:
            continue
        bound.append(dim.paradigm)
        seen_paradigms.add(dim.paradigm)
        dims_bound.append(dim.key)
        values[dim.key] = (val[:24] if isinstance(val, str) else str(val)[:40])
    return {"concept": name, "bound": bound, "dimensions": dims_bound, "values": values}
