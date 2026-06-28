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

    section(f"ADIM 5: YAPI ARAMA — eigenvalue → SMILES")

    # Eigenvalue spektrumu → en yakın moleküler yapı (W2 minimizasyon)
    # produce(μ_drug) fragment kütüphanesini tarar
    try:
        prod = ai.produce_math(disease_numbers, build=True, healthy=healthy_numbers)
        smiles = getattr(prod, "designed_smiles", "") or ""
        n_atoms = getattr(prod, "n_atoms", 0)
        coherent = getattr(prod, "structure_coherent", False)
    except Exception as e:
        smiles = ""
        n_atoms = 0
        coherent = False
        print(f"  Yapı arama hatası: {e}")

    if smiles:
        print(f"  ✓ SMILES bulundu: {smiles}")
        print(f"    Atom sayısı: {n_atoms} | Yapısal uyum: {coherent}")
    else:
        # Fallback: eigenvalue büyüklüğünden tahmin et hangi scaffold yakın
        print(f"  ~ Direkt eşleşme bulunamadı — eigenvalue spektrumundan scaffold tahmini:")
        max_eig = max(abs(e) for e in eigs) if eigs else 0
        if max_eig < 10:
            smiles = "c1ccccc1"           # benzene — küçük aromatik
            label_s = "benzene (küçük aromatik çekirdek)"
        elif max_eig < 30:
            smiles = "c1ccc2[nH]cnc2c1"  # benzimidazole — orta
            label_s = "benzimidazole (orta yapı, kinaz inhibitörü çekirdeği)"
        elif max_eig < 60:
            smiles = "c1ccc2ncccc2c1"    # quinoline — büyük
            label_s = "quinoline (büyük aromatik, ilaç scaffold)"
        else:
            smiles = "Cn1cnc2c1c(=O)n(c(=O)n2C)C"  # caffeine — karmaşık
            label_s = "xanthine çekirdeği (max_eig={:.1f})".format(max_eig)
        print(f"    → {smiles}  [{label_s}]")

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
