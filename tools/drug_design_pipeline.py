"""
İlaç Tasarım Pipeline — Hastalıktan 3D Moleküle
=================================================
Adımlar:
  1. Hastalık verisi (sayılar) → κ_disease
  2. Sağlıklı referans (sayılar) → κ_healthy
  3. κ_drug = κ_healthy ⊟ κ_disease (Voiculescu serbest dekonvolüsyon)
  4. μ_drug → eigenvalue spektrum (İLACIN KENDİSİ — saf matematik)
  5. Eigenvalue spektrumuna en yakın moleküler yapı → SMILES
  6. SMILES → 3D SDF (RDKit ETKDGv3 + MMFF94)

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


def _scaffold_eigenvalues(smiles: str) -> list[float]:
    """Scaffold SMILES → G=AᵀA eigenvalue spektrumu (moleküler Laplacian)."""
    try:
        from rdkit import Chem
        from rdkit.Chem import rdmolops
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


def _w2_distance(a: list[float], b: list[float]) -> float:
    """Wasserstein-2 mesafesi iki eigenvalue spektrumu arasında."""
    if not a or not b:
        return float("inf")
    import numpy as np
    la, lb = sorted(a, reverse=True), sorted(b, reverse=True)
    n = min(len(la), len(lb))
    return float(np.sqrt(sum((la[i] - lb[i]) ** 2 for i in range(n)) / n))


def _match_scaffold(target_eigs: list[float], weights: list[float]) -> str:
    """En yakın scaffold'u W2 mesafesiyle bul."""
    # Ağırlıklı hedef spektrum
    target = sorted([e * w for e, w in zip(target_eigs, weights)], reverse=True)
    best_smi, best_d = _SCAFFOLDS[0][1], float("inf")
    for name, smi in _SCAFFOLDS:
        eigs = _scaffold_eigenvalues(smi)
        d = _w2_distance(target, eigs)
        if d < best_d:
            best_d, best_smi = d, smi
            best_name = name
    print(f"    W2 mesafesi: {best_d:.4f} → {best_name}")
    return best_smi


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

    section(f"ADIM 1-4: MATEMATİK — {label}")

    # 1. Uzay koordinatları
    disease_ms  = build_mini_space(disease_numbers)
    healthy_ms  = build_mini_space(healthy_numbers)

    print(f"  Hastalık uzay koordinatı  → β={disease_ms.beta}, ⟨r⟩={disease_ms.r_ratio:.4f}")
    print(f"  Sağlıklı uzay koordinatı  → β={healthy_ms.beta}, ⟨r⟩={healthy_ms.r_ratio:.4f}")
    print()

    # 2-4. produce_math: κ_disease → κ_drug → eigenvalues
    math_drug = ai.produce_math(disease_numbers, build=False, healthy=healthy_numbers)
    print(math_drug.summary())

    if not math_drug.realizable:
        print(f"  ✗ Gerçeklenebilir değil (gap={math_drug.realizability_gap:.4f}) — pipeline durdu.")
        return

    eigs = math_drug.eigenvalues
    weights = math_drug.weights
    print(f"  ✓ İLACIN SPEKTRUMU: eigenvalues={[round(e,3) for e in eigs]}")
    print(f"    ağırlıklar={[round(w,4) for w in weights]}")

    section(f"ADIM 5: YAPI ARAMA — eigenvalue → SMILES (W2 scaffold eşleştirme)")

    smiles = _match_scaffold(eigs, weights)
    n_atoms = _count_atoms(smiles)
    print(f"  ✓ En yakın scaffold: {smiles}")
    print(f"    Atom sayısı: {n_atoms}")

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
