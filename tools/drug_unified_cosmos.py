"""
Unified Drug Cosmos — Tek Uzayda Hastalık → İlaç → Sağlık
==========================================================
Tek bir unified uzay: DNA + RNA + MOL + PRO + ADME + TGT + SYN + PKT + DIS + HLT

Kontroller:
  1. Unified uzayın kritik çizgi üzerinde olup olmadığı (Li + Λ≤0)
  2. Hastalık Cosmos yörüngesi T₀→T₁₀
  3. İlaç hesabı (κ_healthy ⊟ κ_disease) — unified uzaydan
  4. (Hastalık + İlaç) Cosmos yörüngesi T₀→T₁₀
  5. Geçmiş→Gelecek: her epoch'ta sağlığa yakınsama kontrolü
"""
import sys, os
sys.path.insert(0, "src")
sys.path.insert(0, ".")

import tantrium
from tools.drug_domain_data import (
    DRUG_DOMAIN_LAYERS, all_layers_flat,
    DISEASE_BIOMARKERS, HEALTHY_HOMEOSTASIS, PROTEIN_POCKET_DATA,
    MRNA_MFE_VALUES, HUMAN_PROTEOME_AA_FREQ,
)
from tantrium.core.mini_space import build_mini_space
from tantrium.cosmos import run_cosmos

W = 70

def section(title):
    print()
    print("═" * W)
    print(f"  {title}")
    print("─" * W)

def critical_line_check(ms, label):
    """Li kriterleri + Λ (de Bruijn-Newman) kontrolü."""
    li_ok = all(e > 0 for e in ms.eigenvalues[:4]) if hasattr(ms, 'eigenvalues') else True
    lambda_ok = ms.rh.lambda_val <= 0 if hasattr(ms.rh, 'lambda_val') else True
    on_line = li_ok and lambda_ok
    symbol = "✓ KRİTİK ÇİZGİ" if on_line else "✗ çizgi dışı"
    print(f"  {label:<30} β={ms.beta}  ⟨r⟩={ms.r_ratio:.4f}  {symbol}")
    return on_line

def cosmos_trajectory(numbers, label, n_epochs=11):
    """Cosmos T₀→T₁₀ yörüngesi — her epoch için kritik çizgi ve ⟨r⟩."""
    cosmos = run_cosmos(seed=numbers, inflation_steps=10, n_c=6)
    epochs = cosmos.epochs if hasattr(cosmos, 'epochs') else []

    print(f"\n  ── {label} yörüngesi ──")
    print(f"  {'Epoch':<6} {'⟨r⟩':>7} {'β':>4} {'Li₁':>8} {'Λ':>10} {'Kritik':>8}")
    print(f"  {'─'*6} {'─'*7} {'─'*4} {'─'*8} {'─'*10} {'─'*8}")

    for i, epoch in enumerate(epochs[:n_epochs]):
        ms_e = getattr(epoch, 'mini_space', None)
        if ms_e is None:
            continue
        li1 = ms_e.eigenvalues[0] if hasattr(ms_e, 'eigenvalues') and ms_e.eigenvalues else float('nan')
        try:
            lam = float(ms_e.rh.lambda_val) if hasattr(ms_e.rh, 'lambda_val') else float('nan')
        except Exception:
            lam = float('nan')
        on_line = (li1 > 0 if li1 == li1 else False) and (lam <= 0 if lam == lam else False)
        mark = "✓" if on_line else "✗"
        print(f"  T{i:<5} {ms_e.r_ratio:>7.4f} {ms_e.beta:>4}  {li1:>8.3f}  {lam:>10.4f}  {mark}")

    # Son durum
    final_ms = epochs[-1].mini_space if epochs and hasattr(epochs[-1], 'mini_space') else None
    return cosmos, final_ms

def combine_numbers(*lists):
    """Birden fazla sayı listesini birleştir."""
    result = []
    for lst in lists:
        result.extend(lst)
    return result


def main():
    ai = tantrium.AI()

    print()
    print("═" * W)
    print("  UNİFİED DRUG COSMOS")
    print("  Tek uzay: DNA+RNA+MOL+PRO+ADME+TGT+SYN+PKT+DIS+HLT")
    print("═" * W)

    # ── 1. Unified uzayı kur ──────────────────────────────────────────────────
    section("ADIM 1: UNİFİED UZAY — 15 KATMAN, ~500 SAYI")

    unified_numbers = all_layers_flat()
    ms_unified = build_mini_space(unified_numbers)

    print(f"  Toplam sayı : {len(unified_numbers)}")
    print(f"  Katman sayısı: {len(DRUG_DOMAIN_LAYERS)}")
    for name, data in DRUG_DOMAIN_LAYERS.items():
        ms_l = build_mini_space(data)
        ens = "GUE" if ms_l.beta >= 1.5 else "GOE"
        print(f"    {name:<22} n={len(data):3d}  {ens}  ⟨r⟩={ms_l.r_ratio:.4f}")

    print()
    print(f"  UNİFİED UZAY:")
    critical_line_check(ms_unified, "Unified uzay")

    # ── 2. Hastalık sinyali uzayı ─────────────────────────────────────────────
    section("ADIM 2: HASTALAYIK SİNYALİ — kritik çizgi kontrolü")

    # Hastalık = disease biomarkers + mRNA MFE (ölçülen bozulma)
    disease_numbers = DISEASE_BIOMARKERS + MRNA_MFE_VALUES[:8]
    healthy_numbers = HEALTHY_HOMEOSTASIS + HUMAN_PROTEOME_AA_FREQ[:8]

    ms_disease = build_mini_space(disease_numbers)
    ms_healthy = build_mini_space(healthy_numbers)

    print(f"  Hastalık sinyali  ({len(disease_numbers)} sayı):")
    critical_line_check(ms_disease, "  hastalık")
    print(f"  Sağlıklı referans ({len(healthy_numbers)} sayı):")
    critical_line_check(ms_healthy, "  sağlıklı")

    # ── 3. İlaç hesabı — unified uzaydan ─────────────────────────────────────
    section("ADIM 3: İLAÇ = κ_sağlıklı ⊟ κ_hastalık (unified uzay içinde)")

    math_drug = ai.produce_math(disease_numbers, build=False, healthy=healthy_numbers)
    print(math_drug.summary())

    if not math_drug.realizable:
        print(f"  ✗ Gerçeklenebilir değil (gap={math_drug.realizability_gap:.4f})")
        print("    → Hastalık sinyali farklı kombinasyon denenecek...")
        # Fallback: sadece mRNA + AA freq
        disease_numbers = MRNA_MFE_VALUES[:8]
        healthy_numbers = HUMAN_PROTEOME_AA_FREQ[:8]
        math_drug = ai.produce_math(disease_numbers, build=False, healthy=healthy_numbers)
        print(math_drug.summary())

    eigs = math_drug.eigenvalues
    print(f"  ✓ İLACIN SPEKTRUMU: {[round(e,3) for e in eigs]}")
    print(f"    Gerçeklenebilir  : {math_drug.realizable} (gap={math_drug.realizability_gap:.6f})")

    # ── 4. Hastalık Cosmos yörüngesi ─────────────────────────────────────────
    section("ADIM 4: HASTALAYIK COSMOS YÖRÜNGESİ T₀→T₁₀ (geçmişten geleceğe)")

    try:
        cosmos_dis, final_dis = cosmos_trajectory(disease_numbers, "HASTALIK")
    except Exception as e:
        print(f"  [Cosmos yörüngesi atlandı: {e}]")
        cosmos_dis, final_dis = None, None

    # ── 5. Sağlıklı Cosmos yörüngesi ─────────────────────────────────────────
    section("ADIM 5: SAĞLIKLI COSMOS YÖRÜNGESİ T₀→T₁₀ (referans)")

    try:
        cosmos_hlt, final_hlt = cosmos_trajectory(healthy_numbers, "SAĞLIKLI")
    except Exception as e:
        print(f"  [Cosmos yörüngesi atlandı: {e}]")
        cosmos_hlt, final_hlt = None, None

    # ── 6. İlaç uygulandı: (hastalık + ilaç eigenvalues) Cosmos ─────────────
    section("ADIM 6: (HASTALIK + İLAÇ) COSMOS YÖRÜNGESİ — düzelme görülüyor mu?")

    # İlaç eigenvalue'larını hastalık sayılarına ekliyoruz — spektral katkı
    drug_corrected = disease_numbers + [abs(e) for e in eigs]
    ms_corrected = build_mini_space(drug_corrected)

    print(f"  İlaç uygulandıktan sonra uzay:")
    critical_line_check(ms_corrected, "  hastalık+ilaç")

    try:
        cosmos_cor, final_cor = cosmos_trajectory(drug_corrected, "HASTALIK+İLAÇ")
    except Exception as e:
        print(f"  [Cosmos yörüngesi atlandı: {e}]")
        cosmos_cor, final_cor = None, None

    # ── 7. Karşılaştırma: sağlığa yakınsadı mı? ──────────────────────────────
    section("ADIM 7: KARŞILAŞTIRMA — hastalık vs hastalık+ilaç vs sağlıklı")

    print(f"  {'Durum':<22} {'β':>4}  {'⟨r⟩':>7}  {'RH grade':>9}  {'Kritik':>8}")
    print(f"  {'─'*22} {'─'*4}  {'─'*7}  {'─'*9}  {'─'*8}")

    rows = [
        ("Sağlıklı (hedef)",   ms_healthy),
        ("Hastalık (başlangıç)", ms_disease),
        ("Hastalık + İlaç",    ms_corrected),
        ("Unified uzay",       ms_unified),
    ]

    for label, ms in rows:
        try:
            grade = float(ms.rh.grade())
        except Exception:
            grade = float('nan')
        try:
            lam = float(ms.rh.lambda_val) if hasattr(ms.rh, 'lambda_val') else float('nan')
        except Exception:
            lam = float('nan')
        li1 = ms.eigenvalues[0] if hasattr(ms, 'eigenvalues') and ms.eigenvalues else float('nan')
        on_line = (li1 > 0 if li1 == li1 else False) and (lam <= 0 if lam == lam else False)
        mark = "✓" if on_line else "✗"
        print(f"  {label:<22} {ms.beta:>4}  {ms.r_ratio:>7.4f}  {grade:>9.4f}  {mark}")

    # ── 8. Protein cep uyumu kontrolü ────────────────────────────────────────
    section("ADIM 8: PROTEİN CEP UYUMU — ilaç spectral sınıfı vs cep")

    ms_pocket = build_mini_space(PROTEIN_POCKET_DATA)
    print(f"  Protein cep uzayı:")
    critical_line_check(ms_pocket, "  cep (PKT)")

    # Transport: ilaç eigenvalues → cep eigenvalues
    try:
        cert = ai.transport(str(eigs[0]), str(PROTEIN_POCKET_DATA[0]))
        print(f"  İlaç↔Cep transport: {cert.verdict if hasattr(cert, 'verdict') else cert}")
    except Exception as e:
        # Transport direkt sayı listesi üzerinden
        print(f"  İlaç eigenvalue  ⟨r⟩: ilaç β={ms_corrected.beta}")
        print(f"  Protein cep      ⟨r⟩: cep  β={ms_pocket.beta}")
        match = abs(ms_corrected.r_ratio - ms_pocket.r_ratio)
        print(f"  Spektral mesafe (⟨r⟩): {match:.4f}  {'← yakın' if match < 0.1 else ''}")

    # ── 9. Özet ──────────────────────────────────────────────────────────────
    section("ÖZET")

    dis_r = ms_disease.r_ratio
    cor_r = ms_corrected.r_ratio
    hlt_r = ms_healthy.r_ratio

    correction = abs(cor_r - hlt_r) < abs(dis_r - hlt_r)
    print(f"  Hastalık ⟨r⟩         : {dis_r:.4f}")
    print(f"  Hastalık+İlaç ⟨r⟩   : {cor_r:.4f}")
    print(f"  Sağlıklı ⟨r⟩ (hedef): {hlt_r:.4f}")
    print()
    if correction:
        diff_before = abs(dis_r - hlt_r)
        diff_after  = abs(cor_r - hlt_r)
        pct = (1 - diff_after / diff_before) * 100 if diff_before > 0 else 0
        print(f"  ✓ İlaç sağlığa {pct:.1f}% yakınsattı")
        print(f"  ✓ Uzayda hastalık düzeltmesi GÖRÜLDÜ")
    else:
        print(f"  ✗ Bu ilaç bu metrikle sağlığa yakınsamadı")
        print(f"    (farklı hastalık/sağlıklı sayıları denenebilir)")

    print()
    print("═" * W)
    print("  Unified Cosmos tamamlandı.")
    print("  DNA+RNA+MOL+PRO+ADME+TGT+SYN+PKT+DIS+HLT → tek uzay → ilaç")
    print("═" * W)


if __name__ == "__main__":
    main()
