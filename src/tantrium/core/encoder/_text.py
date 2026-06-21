"""String / SMILES / structured-data → matrix and moment paths.

The string path is pure math: a valid SMILES goes to a bigram (or molecular
graph) matrix, any other string hashes deterministically to signature moments
(position + codepoint, no language / similarity / meaning layer). Also hosts
the numeric-sequence helpers, the dict-adjacency builder, and the fast
power-moment path.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Sequence

from ._linalg import _sequence_to_hankel_matrix

# ─── Numeric sequence helpers ──────────────────────────────────────────────

def _text_to_bigram_matrix(text: str, label_aware: bool = False) -> list[list[Fraction]]:
    """Text → character bigram transition matrix (row-normalized).

    A[i][j] = P(char j follows char i) in the text.
    This is a stochastic matrix — its spectral distribution encodes
    the topology of the language sample: which transitions are common,
    which structures repeat.

    label_aware=True: köşegene küçük ağırlıklı karakter codepoint kimliği ekler,
    satır yeniden normalize edilir (stokastik kalır). Bu, harf KİMLİĞİNİ
    spektruma katar — "pbjw" ve "hame" (ikisi de 4 ayrı karakterli yol grafı)
    aksi halde AYNI permütasyon spektrumuna, aynı momentlere çöker (çakışma).

    SINIR: protein/glucose (7 char, tam çeşitlilik, yol-grafı izomorfizm) bu modda
    L1 ≈ 2.6e-3 marj — ince ama mevcut. Kökten çözüm: bigram yerine N-gram veya
    pozisyon-hash matrisi gerekir (F5 görev listesinde, manifold migrasyonu gerektirir).

    MANIFOLD UYUMU: manifold.json bu mod AÇIKken oluşturuldu (encoder.py:450,458).
    """
    chars = sorted(set(text))
    if not chars:
        return [[Fraction(1)]]
    c2i = {c: i for i, c in enumerate(chars)}
    n = len(chars)
    counts: list[list[int]] = [[0] * n for _ in range(n)]
    for a, b in zip(text, text[1:]):
        counts[c2i[a]][c2i[b]] += 1
    if not label_aware:
        matrix: list[list[Fraction]] = []
        for row in counts:
            total = sum(row)
            if total == 0:
                matrix.append([Fraction(1, n)] * n)
            else:
                matrix.append([Fraction(v, total) for v in row])
        return matrix
    # label_aware: köşegene küçük codepoint kimliği + satır yeniden normalize
    _IDENT_W = Fraction(1, 64)
    matrix = []
    for i, row in enumerate(counts):
        ident = _IDENT_W * Fraction(min(ord(chars[i]), 0x2FFF), 0x3000)
        frow = [Fraction(v) for v in row]
        frow[i] += ident
        total = sum(frow)
        if total == 0:
            matrix.append([Fraction(1, n)] * n)
        else:
            matrix.append([v / total for v in frow])
    return matrix


def _is_valid_smiles(s: str) -> bool:
    """RDKit ile geçerli SMILES mi? Geçerliyse text_signature yolunu atla."""
    try:
        from rdkit import Chem
        return Chem.MolFromSmiles(s) is not None
    except Exception:
        return False


_DNA_ALPHA = set("ACGT")
_RNA_ALPHA = set("ACGU")
_AA_ALPHA = set("ACDEFGHIKLMNPQRSTVWY")


def _char_signature(c: str) -> float:
    """Karaktere deterministik, iyi-yayılmış [0.3, 1.0] imza değeri.

    a-z codepoint'leri (97-122) dar bir aralıkta; doğrudan kullanılırsa harf
    farkları ezilir (yol-grafı izomorfizmi). Çarpımsal hash ile [0,1)'e geniş
    yayıp [0.3,1.0]'a taşırız → her karakter spektrumda ayırt edilebilir kimlik taşır.
    """
    return 0.3 + 0.7 * (((ord(c) * 2654435761) % 9973) / 9973.0)


def _text_to_signature_moments(
    text: str, num_moments: int = 8, gamma: float = 0.4
) -> list[Fraction] | None:
    """Metin → pozisyon+codepoint imza matrisi → eigenvalue-normalize moment [0,1].

    KÖK ÇÖZÜM (encoder collision): tüm-farklı-karakterli kelime (protein/glucose)
    satır-stokastik bigram'da PERMÜTASYON matrisi = ortogonal → G=PᵀP=I → μ_k≡1
    (hepsi çöker). Ayrıca anagramlar (protein/pointer, listen/silent) aynı harf
    kümesi → köşegen-codepoint AYIRMAZ; SIRA bilgisi şart.

    Çözüm: normalize-EDİLMEMİŞ ağırlıklı bigram —
      A[i][j] = Σ_{a→b geçişleri, pozisyon p}  sig(a)·sig(b)·(1 + γ·p/(L-1))
    sig = karakter kimliği (çakışmayı kırar), p = pozisyon (anagramı kırar).
    Sonra SMILES yolu gibi: G=AᵀA → λ normalize → μ_k=(1/n)Σ(λ_i/λ_max)^k ∈ [0,1].

    Hausdorff [0,1] rejimi — SMILES/algı ile AYNI, domain-blind tutarlı. μ_0=1.
    Döner: Fraction moment listesi; geçersiz/boş metinde None (caller fallback).
    """
    try:
        import numpy as np
        if not text or len(text) < 2:
            return None
        chars = sorted(set(text))
        n = len(chars)
        if n < 1:
            return None
        c2i = {c: i for i, c in enumerate(chars)}
        L = len(text)
        A = np.zeros((n, n), dtype=np.float64)
        denom = max(L - 1, 1)
        for p, (a, b) in enumerate(zip(text, text[1:])):
            A[c2i[a]][c2i[b]] += (
                _char_signature(a) * _char_signature(b) * (1.0 + gamma * p / denom)
            )
        G = A.T @ A
        eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
        max_eig = float(eigs.max()) or 1.0
        if max_eig <= 0:
            return None
        vals = sorted(eigs / max_eig)
        nv = len(vals)
        # Kesin-iç regülarizasyon: empirik λ-ölçüsünü küçük uniform [0,1] ölçüsüyle
        # harmanla. Uniform momentleri 1/(k+1) kesin-iç Hausdorff dizisidir → az-karakterli
        # (rank-deficient) kelimelerde bile Hankel minörleri KESİN pozitif kalır, float→Fraction
        # yuvarlamasına dayanır (ALEPH PSD geçer). _EPS küçük → çakışma ayrımı korunur.
        _EPS = 0.02
        moments: list[Fraction] = [Fraction(1)]
        for k in range(1, num_moments):
            emp = sum(d ** k for d in vals) / nv
            uni = 1.0 / (k + 1)
            mk = (1.0 - _EPS) * emp + _EPS * uni
            moments.append(Fraction(float(mk)).limit_denominator(10 ** 9))
        return moments
    except Exception:
        return None


def _text_extra_dims(text: str) -> list[float]:
    """Metin token için ek sinyal boyutları: uzunluk + karakter çeşitliliği.

    Bu boyutlar moment vektörünün YERİNE GEÇMEZ — tamamlayıcıdır.
    Aynı moment imzasına düşen token'ları ayırt eden hafif sinyal:
      [0] uzunluk_norm = min(len, 50) / 50   → kısa/uzun ayrımı
      [1] çeşitlilik_norm = unique_chars / len → tekrarlı/zengin doku

    Özel token'lar (⟨...⟩, sayısal, ':' içerenler) sıfır döner.
    Not: protein/glucose gibi (7 harf, tam çeşitlilik) temel çakışmalar
    için `label_aware=True` modu gerekir; bu boyutlar FARKLI uzunluk ve
    çeşitlilikteki çakışmaları çözer.
    """
    if not text or not isinstance(text, str):
        return [0.0, 0.0]
    if text.startswith("⟨") or ":" in text:
        return [0.0, 0.0]
    clean = text.strip()
    if not clean:
        return [0.0, 0.0]
    len_norm = min(len(clean), 50) / 50.0
    diversity_norm = len(set(clean.lower())) / max(len(clean), 1)
    return [len_norm, diversity_norm]


def _tokens_to_cooccurrence_matrix(
    tokens: list[str], window: int = 2
) -> list[list[Fraction]]:
    """Token sequence → co-occurrence matrix (normalized).

    A[i][j] = how often token i appears within `window` of token j.
    Normalized by row sum. Captures distributional semantics
    without any LLM, without any embedding — pure counting.
    """
    vocab = sorted(set(tokens))
    if not vocab:
        return [[Fraction(1)]]
    t2i = {t: i for i, t in enumerate(vocab)}
    n = len(vocab)
    counts: list[list[int]] = [[0] * n for _ in range(n)]
    for idx, tok in enumerate(tokens):
        i = t2i[tok]
        for delta in range(1, window + 1):
            if idx + delta < len(tokens):
                j = t2i[tokens[idx + delta]]
                counts[i][j] += 1
                counts[j][i] += 1
    matrix: list[list[Fraction]] = []
    for row in counts:
        total = sum(row)
        if total == 0:
            matrix.append([Fraction(1, n)] * n)
        else:
            matrix.append([Fraction(v, total) for v in row])
    return matrix


def _dict_to_adjacency_matrix(
    data: dict[str, Any]
) -> list[list[Fraction]]:
    """Nested dict → adjacency matrix of key-value graph.

    Keys are nodes. An edge exists between key and its value (if the value
    is itself a key at some level). Edge weight = nesting depth (normalized).
    Captures the topology of any structured data.
    """
    all_keys: list[str] = []

    def collect(d: Any, depth: int = 0) -> None:
        if isinstance(d, dict):
            for k, v in d.items():
                key = str(k)
                if key not in all_keys:
                    all_keys.append(key)
                collect(v, depth + 1)
        elif isinstance(d, (list, tuple)):
            for item in d:
                collect(item, depth + 1)

    collect(data)
    if not all_keys:
        return [[Fraction(1)]]
    n = len(all_keys)
    k2i = {k: i for i, k in enumerate(all_keys)}
    counts: list[list[Fraction]] = [[Fraction(0)] * n for _ in range(n)]

    def fill(d: Any, parent: str | None, depth: int) -> None:
        if isinstance(d, dict):
            for k, v in d.items():
                key = str(k)
                if parent is not None:
                    w = Fraction(1, depth + 1)
                    counts[k2i[parent]][k2i[key]] += w
                    counts[k2i[key]][k2i[parent]] += w
                fill(v, key, depth + 1)
        elif isinstance(d, (list, tuple)):
            for item in d:
                fill(item, parent, depth + 1)

    fill(data, None, 0)
    matrix: list[list[Fraction]] = []
    for row in counts:
        total = sum(row)
        if total == 0:
            matrix.append([Fraction(1, n)] * n)
        else:
            matrix.append([v / total for v in row])
    return matrix


# Hankel matris kenar uzunluğu üst sınırı. Üssü O(n³) Fraction aritmetiği
# olduğundan uzun diziler (DNA, sinyaller) burada downsample edilir.
_MAX_HANKEL_DIM = 32


def _downsample(seq: list[Fraction], target_len: int) -> list[Fraction]:
    """Diziyi target_len elemanlık bucket ortalamalarına indirge.

    Spektral dağılımı korur (bucket ortalaması = yerel ölçü yoğunluğu),
    matris boyutunu sınırlar. O(n³) Fraction üssü patlamasını önler.
    """
    n = len(seq)
    if n <= target_len:
        return seq
    out: list[Fraction] = []
    for i in range(target_len):
        lo = (i * n) // target_len
        hi = max(lo + 1, ((i + 1) * n) // target_len)
        chunk = seq[lo:hi]
        out.append(sum(chunk) / len(chunk))
    return out


def _numbers_to_matrix(seq: Sequence[float | int | Fraction]) -> list[list[Fraction]]:
    """Numeric sequence → normalized Hankel matrix.

    The sequence is already a moment sequence — we just normalize it
    so μ_0 = 1 (probability normalization) and convert to Fraction.
    If all values are zero, returns identity.

    Uzun diziler downsample edilir: Hankel kenarı ≤ _MAX_HANKEL_DIM
    (matris üssü O(n³) Fraction → büyük n'de saatlerce sürerdi).
    """
    fracs = [Fraction(v).limit_denominator(10 ** 9) for v in seq]
    total = sum(abs(f) for f in fracs)
    if total == 0:
        return [[Fraction(1)]]
    normalized = [f / total for f in fracs]
    # Hankel kenarı = (len+1)//2 → sınırı aşıyorsa diziyi indirge
    max_seq_len = 2 * _MAX_HANKEL_DIM - 1
    if len(normalized) > max_seq_len:
        normalized = _downsample(normalized, max_seq_len)
        # downsample sonrası yeniden normalize (toplam = 1 korunsun)
        s2 = sum(abs(f) for f in normalized)
        if s2 != 0:
            normalized = [f / s2 for f in normalized]
    return _sequence_to_hankel_matrix(normalized)


# ─── Hızlı power-moment yolu (uzun sayısal diziler) ──────────────────────────

# Bu uzunluğun üzerindeki sayısal diziler exact matris üssü yerine doğrudan
# güç momenti ile kodlanır (Fraction payda patlamasını önler).
_POWER_MOMENT_THRESHOLD = 16


def _try_power_moments(input: Any, num_moments: int) -> "list[Fraction] | None":
    """Uzun sayısal dizi ise μ_k = ort(x^k) doğrudan hesapla, yoksa None.

    Normalleştirme: dizi [0,1]'e ölçeklenir → μ₀=1 sabit, μ_k ∈ [0,1].
    Bu DNA/zeta analizindeki kodlama ile birebir tutarlıdır.
    PSD garantisi: x∈[0,1] için {μ_k = ort(x^k)} geçerli Hausdorff moment
    dizisidir → Hankel PSD → Aleph geçer.
    """
    if not isinstance(input, (list, tuple)) or len(input) <= _POWER_MOMENT_THRESHOLD:
        return None
    if not all(isinstance(x, (int, float, Fraction)) for x in input):
        return None

    vals = [float(x) for x in input]
    mn, mx = min(vals), max(vals)
    span = mx - mn
    if span > 0:
        data = [(x - mn) / span for x in vals]
    else:
        data = [0.5] * len(vals)

    n = len(data)
    moments_raw = [1.0]  # μ₀
    for k in range(1, num_moments):
        moments_raw.append(sum(x ** k for x in data) / n)
    return [Fraction(m).limit_denominator(10 ** 9) for m in moments_raw]


# ─── SMILES Morgan fingerprint encoding ─────────────────────────────────────

def _smiles_to_graph_moments(smiles: str, num_moments: int = 8) -> list[Fraction] | None:
    """SMILES → atom-bağ adjacency matrisi → graf spektrumu → Hausdorff momentler.

    Molekül bir graftur — bunu DOĞRUDAN encode ediyoruz:
      A[i][j] = bağ derecesi (single=1, double=2, triple=3, aromatic=1.5)
      A[i][i] = atom elektronegatifliği (C=1.0, N=1.3, O=1.6, F=2.0, ...)
      G = A^T * A → her zaman PSD, eigenvalues = grafın spektral izleri
      Normalized eigenvalues ∈ [0,1] → geçerli Hausdorff moment dizisi

    HARF benzerliği değil, MOLEKÜLER YAPI topolojisi:
      - Farklı bağ yapısı → farklı graf spektrumu → farklı momentler
      - Benzer topoloji → benzer spektrum → transport sertifikası
    """
    try:
        import numpy as np
        from rdkit import Chem

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        n = mol.GetNumAtoms()
        if n < 2:
            return None

        BOND_ORDER = {
            Chem.rdchem.BondType.SINGLE:   1.0,
            Chem.rdchem.BondType.DOUBLE:   2.0,
            Chem.rdchem.BondType.TRIPLE:   3.0,
            Chem.rdchem.BondType.AROMATIC: 1.5,
        }
        ATOM_EN = {6: 1.0, 7: 1.3, 8: 1.6, 9: 2.0,
                   16: 1.1, 17: 1.4, 35: 1.3, 15: 1.1, 53: 1.2}

        A = np.zeros((n, n))
        for bond in mol.GetBonds():
            i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            w = BOND_ORDER.get(bond.GetBondType(), 1.0)
            A[i, j] = w
            A[j, i] = w
        for i in range(n):
            A[i, i] = ATOM_EN.get(mol.GetAtomWithIdx(i).GetAtomicNum(), 1.0)

        G = A.T @ A
        eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
        max_eig = eigs.max() or 1.0
        atoms = sorted(eigs / max_eig)

        moments: list[Fraction] = [Fraction(1)]
        for k in range(1, num_moments):
            mk = sum(d ** k for d in atoms) / len(atoms)
            moments.append(Fraction(mk).limit_denominator(10 ** 9))
        return moments
    except Exception:
        return None


# Backward-compat alias
def _smiles_molecular_moments(smiles: str, num_moments: int = 8) -> list[Fraction] | None:
    return _smiles_to_graph_moments(smiles, num_moments)


# ── KOD MODALİTESİ (ASI §12 P1) — kod = formal dil = AST grafı = topoloji ──
# Açık kod işaretleri (tek kelime/cümle elenir → metin yoluna düşer).
_CODE_MARKERS = ("def ", "return", "import ", "class ", "lambda ", "for ", "while ",
                 "elif ", "yield ", "assert ", "with ", "print(", "if ", "raise ")


def _smiles_full_eigenvalues(smiles: str) -> list[float] | None:
    """Full n×n molecular adjacency+diagonal eigenvalues, normalized to [0,1].

    Returns the actual graph spectrum — aspirin (27 atoms) and salicylic acid
    (15 atoms) produce genuinely different cell lists for dyadic transport.
    """
    try:
        import numpy as np
        from rdkit import Chem

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        n = mol.GetNumAtoms()
        if n < 2:
            return None

        BOND_ORDER = {
            Chem.rdchem.BondType.SINGLE:   1.0,
            Chem.rdchem.BondType.DOUBLE:   2.0,
            Chem.rdchem.BondType.TRIPLE:   3.0,
            Chem.rdchem.BondType.AROMATIC: 1.5,
        }
        ATOM_EN = {6: 1.0, 7: 1.3, 8: 1.6, 9: 2.0,
                   16: 1.1, 17: 1.4, 35: 1.3, 15: 1.1, 53: 1.2}

        A = np.zeros((n, n))
        for bond in mol.GetBonds():
            i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            w = BOND_ORDER.get(bond.GetBondType(), 1.0)
            A[i, j] = w
            A[j, i] = w
        for i in range(n):
            A[i, i] = ATOM_EN.get(mol.GetAtomWithIdx(i).GetAtomicNum(), 1.0)

        G = A.T @ A
        eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
        max_eig = eigs.max() or 1.0
        return sorted((eigs / max_eig).tolist(), reverse=True)
    except Exception:
        return None


def _smiles_to_descriptor_matrix(smiles: str) -> list[list[Fraction]]:
    """SMILES → molecular moments → Hankel matrix (for structure extraction)."""
    moments = _smiles_molecular_moments(smiles)
    if moments is None:
        return _text_to_bigram_matrix(smiles)
    # Moments are now a valid Hausdorff sequence → Hankel is PSD
    return _sequence_to_hankel_matrix(moments)


# Keep old name as alias so existing callers still work
def _smiles_to_morgan_matrix(smiles: str, n_bits: int = 64) -> list[list[Fraction]]:
    return _smiles_to_descriptor_matrix(smiles)
