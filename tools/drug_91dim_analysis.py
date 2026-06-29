"""
91-Dim Analiz — Hastalık vs İlaç vs Sağlık
============================================
Her boyut ayrı ayrı: ne değişti, ne düzeldi, ne hâlâ bozuk?

Grup 1  [0:16]  — 16 moment
Grup 2  [16:30] — 14 RH nicel (pivot, cross-ratio, kümülant, Λ, rank, grade)
Grup 3  [30:37] — 7 pozitiflik bayrağı (bariyerler)
Grup 4  [37:41] — 4 Li katsayısı (kritik çizgi)
Grup 5  [41:45] — 4 GOE/GUE zaman ekseni
Grup 6  [45:91] — 46 paradigma imzası
"""
import sys, math
sys.path.insert(0, "src")
sys.path.insert(0, ".")

import tantrium
from tools.drug_domain_data import MRNA_MFE_VALUES, HUMAN_PROTEOME_AA_FREQ
from tantrium.core.mini_space import build_mini_space

W = 72

GRUP_ETIKETLER = {
    # [dim_start, dim_end, isim, boyutlar]
    "G1_MOMENT":    (0,  16, "MOMENT",      [f"μ{i}" for i in range(16)]),
    "G2_RH":        (16, 30, "RH NİCEL",   ["pivot1","pivot2","pivot3","pivot4",
                                              "cr1","cr2","cr3",
                                              "κ1","κ2","κ3","κ4",
                                              "Λ","rank","grade"]),
    "G3_POZ":       (30, 37, "POZİTİFLİK", ["hankel_psd","stieltjes_psd",
                                              "pivots_pos","cr_pos","first5_pos",
                                              "hamburger","stieltjes_cert"]),
    "G4_LI":        (37, 41, "Lİ KRİTER",  ["Li₁","Li₂","Li₃","Li₄"]),
    "G5_SPEKTRAL":  (41, 45, "SPEKTRAL",   ["⟨r⟩","goe_dist","gue_dist","β/2"]),
    "G6_PARADIGMA": (45, 91, "PARADİGMA",  [f"P{i}" for i in range(46)]),
}

def sign(v_dis, v_hlt, v_cor):
    """İlaç doğru yönde mi gitti?"""
    dis_gap = v_dis - v_hlt
    cor_gap = v_cor - v_hlt
    if abs(dis_gap) < 1e-9:
        return " ="
    improved = abs(cor_gap) < abs(dis_gap)
    return " ↑" if improved else " ↓"

def pct(v_dis, v_hlt, v_cor):
    """Düzelme yüzdesi."""
    dis_gap = abs(v_dis - v_hlt)
    cor_gap = abs(v_cor - v_hlt)
    if dis_gap < 1e-9:
        return "  —  "
    imp = (1 - cor_gap / dis_gap) * 100
    return f"{imp:+5.1f}%"


def main():
    ai = tantrium.AI()

    disease_numbers  = MRNA_MFE_VALUES[:8]
    healthy_numbers  = HUMAN_PROTEOME_AA_FREQ[:8]

    # İlaç hesabı
    math_drug = ai.produce_math(disease_numbers, build=False, healthy=healthy_numbers)
    eigs = math_drug.eigenvalues

    # Üç uzay
    ms_dis = build_mini_space(disease_numbers)
    ms_hlt = build_mini_space(healthy_numbers)
    ms_cor = build_mini_space(disease_numbers + [abs(e) for e in eigs])

    v_dis = ms_dis.universe_coordinate()
    v_hlt = ms_hlt.universe_coordinate()
    v_cor = ms_cor.universe_coordinate()

    # Boyut sayısı normalize et
    n = min(len(v_dis), len(v_hlt), len(v_cor), 91)

    print()
    print("═" * W)
    print("  91-DİM ANALİZ: HASTALIK → İLAÇ → SAĞLIK")
    print(f"  İlaç spektrumu: {[round(e,3) for e in eigs]}")
    print("═" * W)

    total_dims = 0
    improved   = 0
    worsened   = 0
    unchanged  = 0
    broken_barriers = []
    fixed_barriers  = []

    for grp_key, (d0, d1, grp_name, labels) in GRUP_ETIKETLER.items():
        d1 = min(d1, n)
        if d0 >= n:
            continue

        print()
        print(f"  ── {grp_name} [dim {d0}:{d1}] ──")
        print(f"  {'Boyut':<14} {'HASTALIK':>9} {'SAĞLIKLI':>9} {'HAŞ+İLAÇ':>9} {'Δ':>6}  {'Düzelme':>7}")
        print(f"  {'─'*14} {'─'*9} {'─'*9} {'─'*9} {'─'*6}  {'─'*7}")

        for i, dim in enumerate(range(d0, d1)):
            label = labels[i] if i < len(labels) else f"d{dim}"
            vd = v_dis[dim]
            vh = v_hlt[dim]
            vc = v_cor[dim]

            total_dims += 1
            s = sign(vd, vh, vc)
            p = pct(vd, vh, vc)

            if s == " ↑":
                improved += 1
            elif s == " ↓":
                worsened += 1
            else:
                unchanged += 1

            # Bayrak boyutları (Grup 3)
            if grp_key == "G3_POZ":
                if vd < 0.5 and vh >= 0.5:
                    broken_barriers.append(label)
                if vd < 0.5 and vc >= 0.5:
                    fixed_barriers.append(label)

            print(f"  {label:<14} {vd:>9.4f} {vh:>9.4f} {vc:>9.4f} {s:>6}  {p:>7}")

    # Özet
    print()
    print("═" * W)
    print(f"  ÖZET — {total_dims} boyut")
    print("─" * W)
    pct_imp = improved / total_dims * 100
    pct_wor = worsened / total_dims * 100
    pct_unc = unchanged / total_dims * 100
    print(f"  ↑ Düzeldi  : {improved:3d} / {total_dims}  ({pct_imp:.1f}%)")
    print(f"  ↓ Kötüleşti: {worsened:3d} / {total_dims}  ({pct_wor:.1f}%)")
    print(f"  = Değişmedi: {unchanged:3d} / {total_dims}  ({pct_unc:.1f}%)")

    if broken_barriers:
        print(f"\n  Hastalıkta kırılan bariyerler : {broken_barriers}")
    if fixed_barriers:
        print(f"  İlaçla onarılan bariyerler   : {fixed_barriers}")

    # En çok bozulan boyutlar
    diffs = [(abs(v_dis[i] - v_hlt[i]), i) for i in range(n)]
    diffs.sort(reverse=True)
    print(f"\n  En çok bozulan 5 boyut (hastalıkta):")
    for gap, idx in diffs[:5]:
        grp = next((g for g, (d0,d1,_,_) in GRUP_ETIKETLER.items() if d0 <= idx < d1), "?")
        s = sign(v_dis[idx], v_hlt[idx], v_cor[idx])
        print(f"    dim[{idx:2d}] gap={gap:.4f}  {grp}  ilaçla{s}")

    print()
    print("═" * W)


if __name__ == "__main__":
    main()
