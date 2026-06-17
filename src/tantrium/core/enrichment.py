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


# Bilinen matematiksel diziler (yasa boyutu için — ağsız, OEIS gerekmez).
_KNOWN_SEQUENCES: dict[str, list[float]] = {
    "fibonacci": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144],
    "lucas": [2, 1, 3, 4, 7, 11, 18, 29, 47, 76, 123],
    "prime": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37],
    "tribonacci": [0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149],
    "catalan": [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862],
    "factorial": [1, 2, 6, 24, 120, 720, 5040, 40320],
    "triangular": [1, 3, 6, 10, 15, 21, 28, 36, 45, 55],
    "square": [1, 4, 9, 16, 25, 36, 49, 64, 81, 100],
    "pentagonal": [1, 5, 12, 22, 35, 51, 70, 92, 117],
}


def fetch_governing_law(name: str, ai) -> list[float] | None:
    """Kavramın YÖNETİCİ YASASINI çıkar (discover_law) → yasa parmak-izi vektörü. İç, ağsız.

    Bilinen matematiksel dizi (fibonacci/prime/lucas...) → değerlerini üret → `ai.discover_law`
    → yasa GÜVENİLİRSE [order, *recurrence, *modes] parmak izi (Fibonacci → φ modları). Matematik
    çekirdeğine bağlanan en GENEL boyut: elmanın büyüme deseni de bir molekülün spektrumu da
    aynı sayı/RH zeminine. DÜRÜST SINIR: oto yalnız bilinen diziler (OEIS 403); başka sayısal iz
    elle `ai.enrich(law_series=...)` ile verilebilir (manuel yol enrich_concept'te)."""
    n = name.lower()
    seq = None
    for key, vals in _KNOWN_SEQUENCES.items():
        if key in n:
            seq = vals
            break
    if seq is None:
        return None
    try:
        ld = ai.discover_law(seq)
    except Exception:
        return None
    if not getattr(ld, "law_holds", False):
        return None
    fp = [float(getattr(ld, "order", 0))]
    fp += [float(x) for x in (getattr(ld, "recurrence", []) or [])]
    fp += [float(x) for x in (getattr(ld, "modes", []) or [])]
    return fp if len(fp) >= 2 else None


def fetch_protein_3d(name: str, ai, *, timeout: float = 10.0, max_res: int = 48) -> "Any":
    """Protein 3D yapısı (AlphaFold) → Cα uzaklık matrisi (katlanma geometrisi). Gen/protein için.

    gen→UniProt accession→AlphaFold PDB→Cα koordinatları→pairwise uzaklık matrisi (katlanmanın
    GERÇEK 3D imzası, diziden BAĞIMSIZ). max_res ile sınırlı (matris küçük). DÜRÜST: yalnız
    PROTEİN — MOLEKÜL/İLAÇ 3D'si ÇEKİLMEZ (çekirdek `produce` ile sıfırdan üretir, dış 3D kirletir)."""
    if not _valid_name(name):
        return None
    acc_data = _get_json(
        "https://rest.uniprot.org/uniprotkb/search?query=gene:" + urllib.parse.quote(name)
        + "+AND+organism_id:9606&format=json&fields=accession&size=1", timeout)
    if not (acc_data and acc_data.get("results")):
        return None
    acc = acc_data["results"][0].get("primaryAccession")
    if not acc:
        return None
    meta = _get_json(f"https://alphafold.ebi.ac.uk/api/prediction/{acc}", timeout)
    if not (isinstance(meta, list) and meta):
        return None
    pdb = _get_text(meta[0].get("pdbUrl", ""), timeout)
    if not pdb:
        return None
    import numpy as np
    coords = []
    for line in pdb.split("\n"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            try:
                coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
        if len(coords) >= max_res:
            break
    if len(coords) < 6:
        return None
    pts = np.array(coords)
    diff = pts[:, None, :] - pts[None, :, :]
    dist = np.sqrt((diff ** 2).sum(-1))      # Cα-Cα uzaklık matrisi (katlanma geometrisi)
    return dist


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


def _bind_law(ai, concept: str, fingerprint: list[float], key: str) -> None:
    """Yasa parmak-izi ([order, recurrence, modes]) → PSD matris → IS_GOVERNED_BY.

    Kavramı YÖNETİCİ DİNAMİĞİNE bağlar (matematik çekirdeği) — Fibonacci→φ. Vektör outer-
    çarpımla PSD matrise (encode_matrix momentleri); modlar/recurrence imzayı taşır."""
    import numpy as np
    v = np.array([float(x) for x in fingerprint], dtype=float)
    nrm = float(np.linalg.norm(v)) or 1.0
    v = v / nrm
    ai.bind_percept(concept, np.outer(v, v), modality="matrix", paradigm="IS_GOVERNED_BY",
                    name=f"⟨percept:{concept}:law⟩")


def _bind_structure3d(ai, concept: str, dist_matrix, key: str) -> None:
    """3D katlanma uzaklık-matrisi → HAS_TOPOLOGY (diziden bağımsız 3D fold imzası)."""
    ai.bind_percept(concept, dist_matrix, modality="matrix", paradigm="HAS_TOPOLOGY",
                    name=f"⟨percept:{concept}:structure3d⟩")


def _bind_sound(ai, concept: str, signal, key: str) -> None:
    """Ses sinyali → HAS_SIGNAL (Wiener-Khinchin moment). Oto-kaynak yok; elle `sound=`."""
    ai.bind_percept(concept, signal, modality="signal", paradigm="HAS_SIGNAL",
                    name=f"⟨percept:{concept}:sound⟩")


# ─── Genişletilebilir boyut REGİSTRY'si ───────────────────────────────────────

@dataclass(frozen=True)
class Dimension:
    key: str                                  # "molecule"/"protein"/"dna"/"properties"/"law"/"structure3d"/"sound"
    paradigm: str                             # HAS_COMPOUND/HAS_DNA/HAS_GEOMETRY/IS_GOVERNED_BY/HAS_TOPOLOGY/HAS_SIGNAL
    fetch: Callable[[str, Any], Any]          # (isim, ai) → gerçek değer veya None (None=oto-fetch yok)
    bind: Callable[[Any, str, Any, str], None]  # (ai, concept, value, key) → bağla
    network: bool = True                      # oto-fetch ağ ister mi (law iç/ağsız)


def _adapt(fn):
    """name-only fetcher'ı (name, ai) imzasına uyarla."""
    return lambda name, ai: fn(name)


# Sıra: kesin-eşleşenler (bio/iç) önce, gevşek (molekül) sonra. Yeni boyut = bir satır.
# MOLEKÜL 3D YOK — çekirdek ilacı `produce` ile sıfırdan üretir; dış 3D molekül kirletir.
_DIMENSIONS: list[Dimension] = [
    Dimension("law", "IS_GOVERNED_BY", fetch_governing_law, _bind_law, network=False),
    Dimension("protein", "HAS_DNA", _adapt(fetch_protein_sequence), _bind_bio),
    Dimension("dna", "HAS_DNA", _adapt(fetch_dna_sequence), _bind_bio),
    Dimension("structure3d", "HAS_TOPOLOGY", fetch_protein_3d, _bind_structure3d),
    Dimension("molecule", "HAS_COMPOUND", _adapt(fetch_molecular_smiles), _bind_molecule),
    Dimension("properties", "HAS_GEOMETRY", _adapt(fetch_physical_properties), _bind_properties),
    # sound: oto-kaynak yok (isimle çekilemez) → fetch None; yalnız elle sound= ile.
    Dimension("sound", "HAS_SIGNAL", lambda name, ai: None, _bind_sound),
]

# Elle-override anahtarları (ağsız test / kullanıcı verisi) → boyut anahtarı eşlemesi.
_MANUAL_ALIASES = {"smiles": "molecule", "protein": "protein", "dna": "dna",
                   "properties": "properties", "law": "law", "structure3d": "structure3d",
                   "sound": "sound"}


def enrich_concept(ai, name: str, *, network: bool = True, dims: list[str] | None = None,
                   **manual) -> dict:
    """Kavramı TÜM uygulanabilir boyutlarda kökle (registry). Tip-farkında, fail-open, idempotent.

    `manual` (smiles=/protein=/dna=/properties=/law=/structure3d=/sound=) elle değer verir
    (ağsız test); yoksa boyut `network` ister ve `network=True` ise fetcher dener. `dims` verilirse
    yalnız o boyutlar. Döner: {concept, bound:[paradigmalar], dimensions:[anahtarlar], values}.
    """
    manual_by_key = {_MANUAL_ALIASES[k]: v for k, v in manual.items()
                     if k in _MANUAL_ALIASES and v is not None}
    bound: list[str] = []
    dims_bound: list[str] = []
    values: dict[str, str] = {}
    for dim in _DIMENSIONS:
        if dims is not None and dim.key not in dims:
            continue
        val = manual_by_key.get(dim.key)
        if val is None and network and dim.network:
            try:
                val = dim.fetch(name, ai)
            except Exception:
                val = None
        elif val is None and not dim.network:        # iç/ağsız boyut (law) — ağ bayrağından bağımsız
            try:
                val = dim.fetch(name, ai)
            except Exception:
                val = None
        if val is None or (isinstance(val, str) and not val):
            continue
        try:
            dim.bind(ai, name, val, dim.key)
        except Exception:
            continue
        bound.append(dim.paradigm)
        dims_bound.append(dim.key)
        values[dim.key] = (val[:24] if isinstance(val, str) else str(val)[:40])
    return {"concept": name, "bound": bound, "dimensions": dims_bound, "values": values}
