"""
İlaç Tasarım Pipeline — Hastalıktan 3D Moleküle
=================================================
Adımlar:
  1. Hastalık verisi (sayılar) → 91-dim universe_coordinate()
  2. Sağlıklı referans (sayılar) → 91-dim universe_coordinate()
  3. Hedef = v_healthy - v_disease (91-dim boşluk)
  4. κ_drug = κ_healthy ⊟ κ_disease (Voiculescu) → gerçeklenebilirlik sertifikası
  5. Her scaffold → 91-dim vektör → Öklid mesafesi → en yakın scaffold
  6. SMILES → 3D SDF (RDKit ETKDGv3 + MMFF94)

91 boyutun TAMAMI kullanılır: moment + pivot + cross-ratio + Li + Λ + GOE/GUE + paradigma.
Dil yok. Harf yalnız en sonda (SMILES/SDF çıktısında).
"""
import sys, os
sys.path.insert(0, "src")
sys.path.insert(0, ".")

import tantrium
from tools.drug_domain_data import (
    MRNA_MFE_VALUES,
    HUMAN_PROTEOME_AA_FREQ,
    KINASE_BINDING_KI_NM,
    DRUG_ADME,
    SYNTHESIS_FREE_ENERGIES_KJ,
)
from tantrium.core.mini_space import build_mini_space
from tantrium.core.molecular_3d import embed_3d_sdf

W = 70
OUT_DIR = "/tmp/tantrium_molecules"
os.makedirs(OUT_DIR, exist_ok=True)

# Bilinen ilaç scaffold'ları + eigenvalue spektrumları (G=AᵀA'dan)
_SCAFFOLDS = [
    ("adenine",         "Nc1ncnc2ncnc12"),
    ("benzimidazole",   "c1ccc2[nH]cnc2c1"),
    ("quinoline",       "c1ccc2ncccc2c1"),
    ("quinazoline",     "c1cnc2ccccc2n1"),
    ("indole",          "c1ccc2[nH]ccc2c1"),
    ("pyrimidine",      "c1ccncn1"),
    ("purine",          "c1ncc2[nH]cnc2n1"),
    ("imidazole",       "c1cn[nH]c1"),          # pyrazole
    ("piperidine",      "C1CCNCC1"),
    ("morpholine",      "C1CCOCC1"),
    ("benzene",         "c1ccccc1"),
    ("naphthalene",     "c1ccc2ccccc2c1"),
    ("caffeine",        "Cn1cnc2c1c(=O)n(c(=O)n2C)C"),
    ("imatinib_core",   "Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C"),
    ("erlotinib_core",  "C#Cc1cccc(Nc2ncnc3cc(OCCO)c(OCC)cc23)c1"),
    ("gefitinib_core",  "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN4CCOCC4"),
]


def _scaffold_laplacian_eigs(smiles: str) -> list[float]:
    """Scaffold SMILES → moleküler Laplacian eigenvalue listesi."""
    try:
        from rdkit import Chem
        import numpy as np
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        n = mol.GetNumAtoms()
        L = np.zeros((n, n))
        for b in mol.GetBonds():
            i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
            L[i, j] = L[j, i] = -1.0
        for i in range(n):
            L[i, i] = -L[i].sum() - L[i, i]
        eigs = sorted(np.linalg.eigvalsh(L), reverse=True)
        return [float(e) for e in eigs if abs(e) > 1e-10]
    except Exception:
        return []


def _scaffold_91dim(smiles: str) -> list[float] | None:
    """Scaffold SMILES → 91-dim universe_coordinate vektörü.

    Moleküler Laplacian eigenvalue'ları → build_mini_space → universe_coordinate().
    Böylece scaffold'un moment/RH/Li/paradigma bilgisi tamamı kullanılır.
    """
    eigs = _scaffold_laplacian_eigs(smiles)
    if not eigs:
        return None
    try:
        ms = build_mini_space(eigs)
        return ms.universe_coordinate()
    except Exception:
        return None


def _euclidean_91(a: list[float], b: list[float]) -> float:
    """İki 91-dim vektör arasında Öklid mesafesi."""
    import math
    n = min(len(a), len(b))
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)))


def _match_scaffold_91dim(v_disease: list[float], v_healthy: list[float]) -> tuple[str, str]:
    """91-dim uzayda en yakın scaffold'u bul.

    Hedef = v_healthy (sağlıklı uzay koordinatı).
    Her scaffold'un 91-dim vektörü hesaplanır, Öklid mesafesiyle karşılaştırılır.
    Scaffold seçimi: moment, pivot, cross-ratio, Li, Λ, GOE/GUE, paradigma hepsini kullanır.
    """
    import math

    # Hedef: sağlıklı uzay koordinatı (drug → disease'i healthy'e taşımalı)
    target = v_healthy

    best_smi, best_name, best_d = _SCAFFOLDS[0][1], _SCAFFOLDS[0][0], float("inf")
    details = []

    for name, smi in _SCAFFOLDS:
        v_scaf = _scaffold_91dim(smi)
        if v_scaf is None:
            continue
        d = _euclidean_91(target, v_scaf)
        details.append((d, name, smi))
        if d < best_d:
            best_d, best_smi, best_name = d, smi, name

    # En iyi 3'ü göster
    details.sort()
    print(f"    91-dim Öklid mesafesi (ilk 3):")
    for d, n, s in details[:3]:
        marker = " ←" if n == best_name else ""
        print(f"      {n:<20} d={d:.4f}{marker}")

    return best_smi, best_name


def _count_atoms(smiles: str) -> int:
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        return mol.GetNumAtoms() if mol else 0
    except Exception:
        return 0


def section(title: str) -> None:
    print()
    print("═" * W)
    print(f"  {title}")
    print("─" * W)


def run_pipeline(disease_numbers: list, healthy_numbers: list,
                 label: str, target_name: str) -> None:

    ai = tantrium.AI()

    section(f"ADIM 1-2: 91-DİM UZAY KOORDİNATI — {label}")

    # 1. Her iki durum için TAM 91-dim universe_coordinate
    disease_ms  = build_mini_space(disease_numbers)
    healthy_ms  = build_mini_space(healthy_numbers)
    v_disease   = disease_ms.universe_coordinate()
    v_healthy   = healthy_ms.universe_coordinate()

    print(f"  Hastalık  91-dim: β={disease_ms.beta}, ⟨r⟩={disease_ms.r_ratio:.4f}, "
          f"Λ={float(disease_ms.rh.lambda_dbn):+.4f}")
    print(f"  Sağlıklı  91-dim: β={healthy_ms.beta}, ⟨r⟩={healthy_ms.r_ratio:.4f}, "
          f"Λ={float(healthy_ms.rh.lambda_dbn):+.4f}")

    # 91-dim boşluk: kaç boyut farklı?
    n_dim = min(len(v_disease), len(v_healthy))
    n_diff = sum(1 for i in range(n_dim) if abs(v_disease[i] - v_healthy[i]) > 1e-6)
    import math
    gap_91 = math.sqrt(sum((v_disease[i]-v_healthy[i])**2 for i in range(n_dim)))
    print(f"  91-dim boşluk : {n_diff}/{n_dim} boyut farklı, Öklid={gap_91:.4f}")
    print()

    # 3-4. Voiculescu dekonvolüsyon → gerçeklenebilirlik sertifikası
    math_drug = ai.produce_math(disease_numbers, build=False, healthy=healthy_numbers)
    print(math_drug.summary())

    if not math_drug.realizable:
        print(f"  ✗ Gerçeklenebilir değil (gap={math_drug.realizability_gap:.4f}) — pipeline durdu.")
        return

    eigs = math_drug.eigenvalues
    print(f"  ✓ İLACIN SPEKTRUMU: eigenvalues={[round(e,3) for e in eigs]}")

    section(f"ADIM 5: YAPI ARAMA — 91-DİM UZAYDA SCAFFOLD EŞLEŞTİRME")
    print(f"  Hedef: sağlıklı 91-dim koordinatı")
    print(f"  Yöntem: scaffold → Laplacian eigs → universe_coordinate() → Öklid mesafesi")
    print()

    smiles, scaffold_name = _match_scaffold_91dim(v_disease, v_healthy)
    n_atoms = _count_atoms(smiles)

    # Seçilen scaffold'un 91-dim vektörünü karşılaştır
    v_scaf = _scaffold_91dim(smiles)
    if v_scaf:
        scaf_gap = math.sqrt(sum((v_healthy[i]-v_scaf[i])**2 for i in range(min(len(v_healthy),len(v_scaf)))))
        print(f"  ✓ Seçilen scaffold: {scaffold_name} → {smiles}")
        print(f"    Atom sayısı : {n_atoms}")
        print(f"    Sağlıklıya 91-dim mesafe: {scaf_gap:.4f}  (hastalık→sağlıklı boşluk={gap_91:.4f})")

    section(f"ADIM 6: 3D YAPI — SMILES → SDF (RDKit ETKDGv3)")

    sdf_path = embed_3d_sdf(
        smiles=smiles,
        name=target_name,
        out_dir=OUT_DIR,
        prefix=f"{target_name}_",
        props={
            "Disease_Signal": str([round(x,2) for x in disease_numbers[:4]]),
            "Drug_Eigenvalues": str([round(e,3) for e in eigs]),
            "Realizability_Gap": str(round(math_drug.realizability_gap, 6)),
            "Pipeline": "Tantrium_produce_math",
        },
        remove_hs=True,
    )

    if sdf_path:
        print(f"  ✓ 3D SDF dosyası: {sdf_path}")
        # İlk satırları göster
        with open(sdf_path) as f:
            lines = f.readlines()[:20]
        print()
        print("  ── SDF içeriği (ilk 20 satır) ──")
        for ln in lines:
            print("    " + ln.rstrip())
    else:
        print("  ✗ 3D SDF üretilemedi (geçersiz SMILES veya RDKit hatası)")


def main():
    print()
    print("═" * W)
    print("  İLAÇ TASARIM PİPELİNE")
    print("  Hastalık (sayılar) → κ → eigenvalue → SMILES → 3D SDF")
    print("═" * W)

    # ── ÖRNEK 1: mRNA hastalık sinyali → protein dengesizliği düzeltici ────────
    run_pipeline(
        disease_numbers=MRNA_MFE_VALUES[:8],       # kanser gen mRNA MFE değerleri
        healthy_numbers=HUMAN_PROTEOME_AA_FREQ[:8], # normal protein AA dengesi
        label="Kanser mRNA → Protein Dengesi Düzeltici",
        target_name="mrna_cancer_drug",
    )

    # ── ÖRNEK 2: ADME hastalık profili → sentez enerji hedefi ────────────────
    run_pipeline(
        disease_numbers=DRUG_ADME[:8],                     # bozuk ADME profili
        healthy_numbers=SYNTHESIS_FREE_ENERGIES_KJ[:8],    # ideal sentez enerjileri
        label="ADME Profili → Sentez-Uyumlu Düzeltici",
        target_name="adme_corrector",
    )

    print()
    print("═" * W)
    print(f"  Pipeline tamamlandı. SDF dosyaları: {OUT_DIR}/")
    print("═" * W)


if __name__ == "__main__":
    main()
