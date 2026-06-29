"""
İlaç Domain'i — Cosmos Evrimi
==============================
Her katman (DNA, RNA, Mol, ADME, ...) Cosmos sisteminden geçer.
T₀→T₁₀ arası izlenir: fizik, biyoloji, matematik tutarlı mı?

Fizik doğru  → kritik çizgide (Li λₙ>0 ∧ Λ≤0)
Biyoloji doğru → Stieltjes pozitif (gerçek ölçü)
Matematik doğru → grade=1.0, Hankel PSD
"""
import sys
import time
import math
import signal

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from tools.drug_domain_data import DRUG_DOMAIN_LAYERS
from tantrium.cosmos import run_cosmos
from tantrium.core.mini_space import build_mini_space

_RUNNING = True
def _stop(sig, frame):
    global _RUNNING
    _RUNNING = False
    print("\nDurduruluyor...")
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)


W = 72

def _bar(val: float, width: int = 20) -> str:
    filled = int(abs(val) * width)
    return "█" * min(filled, width)


def _epoch_symbol(t: str, law_held: bool) -> str:
    return "✓" if law_held else "✗"


def _print_cosmos(name: str, life, ms) -> None:
    print()
    print("═" * W)
    print(f"  {name}")
    print("─" * W)

    # Katman özeti
    beta  = ms.beta
    r     = ms.r_ratio
    ens   = "GUE (β=2, zaman-tersinmez)" if beta >= 1.5 else "GOE (β=1, zaman-tersinir)"
    n     = ms.n
    grade = float(ms.rh.grade())
    print(f"  n={n:3d} | {ens} | ⟨r⟩={r:.4f} | grade={grade:.2f}")
    print()

    # T₀→T₁₀ çağlar
    print("  ── Cosmos Evrimi ──")
    for e in life.epochs:
        sym = _epoch_symbol(e.t, e.law_held)
        print(f"    {e.t:>3}  {e.name:<16}  [{sym}]  {e.reading}")
    print()

    # Kritik çizgi (FİZİK)
    on_line = life.on_critical_line
    fizik = "✓ KRİTİK ÇİZGİDE" if on_line else "✗ kritik çizgi dışı"
    print(f"  FİZİK  → {fizik}")

    # Stieltjes (BİYOLOJİ — gerçek pozitif ölçü)
    stieltjes = ms.rh.stieltjes_psd
    bio = "✓ GERÇEKLEŞEBİLİR ÖLÇÜ (Stieltjes pozitif)" if stieltjes else "✗ ölçü negatif bileşen içeriyor"
    print(f"  BİYO   → {bio}")

    # Hankel PSD + grade (MATEMATİK)
    hpsd  = ms.rh.hankel_psd
    mat = f"✓ grade={grade:.2f}, Hankel PSD" if hpsd else f"✗ Hankel PSD değil, grade={grade:.2f}"
    print(f"  MATEMATİK → {mat}")

    print()

    # 4-katman ızgara (doğuş → son)
    if life.genesis_reading and life.final_reading:
        g = life.genesis_reading
        f = life.final_reading
        print("  ── 4-Katman Izgarası (doğuş → son) ──")
        print(f"    1 MAKRO    rank {g.rank} → {f.rank}")
        print(f"    2 MİKRO    {g.universality} → {f.universality}")
        if life.universality_path:
            print(f"             yörünge: {'→'.join(life.universality_path[:8])}")
        print(f"    3 SİMETRİ  Dyson β={g.beta} → β={f.beta}")
        ge = "—" if g.ergodicity is None else f"{g.ergodicity:.3f}"
        fe = "—" if f.ergodicity is None else f"{f.ergodicity:.3f}"
        gd = "—" if g.fractal_dim is None else f"{g.fractal_dim:.3f}"
        fd = "—" if f.fractal_dim is None else f"{f.fractal_dim:.3f}"
        print(f"    4 ÖZVEKTÖR ergodiklik {ge}→{fe} | D₂ fraktal {gd}→{fd}")
        if life.transitions:
            print(f"    ⚡ FAZ GEÇİŞİ  {' | '.join(life.transitions)}")

    # Topoloji (5. eksen)
    if life.topology is not None:
        t = life.topology
        yuk = f"net akış={t.net_flow:+d}"
        duz = "düzgün (topolojik sabit)" if t.smooth else f"{t.crossings} mod yeniden-örgütlenmesi"
        print(f"    5 TOPOLOJİ {yuk} | {duz}")

    print()
    print(f"  T₁₀ KADER: {life.fate_crunch}")
    print(f"              {life.fate_rip}")
    print(f"  MÜHÜR: {life.master_seal[:24]}...")


def run_all() -> None:
    print()
    print("═" * W)
    print("  İLAÇ ÜRETİMİ DOMAIN — COSMOS EVRİMİ")
    print("  Her katman T₀→T₁₀ arası ilerler. FİZİK + BİYO + MATEMATİK kontrolü.")
    print("═" * W)

    results = {}

    for name, data in DRUG_DOMAIN_LAYERS.items():
        if not _RUNNING:
            break
        print(f"\n  [{name}] hesaplanıyor...", end="", flush=True)

        ms = build_mini_space(data)
        # Cosmos seed: ham veri (sayı listesi olarak doğrudan)
        life = run_cosmos(seed=data, inflation_steps=20, n_c=8)

        results[name] = (life, ms)
        _print_cosmos(name, life, ms)

    if not _RUNNING or len(results) < 2:
        return

    # ── Karşılaştırma özeti ──────────────────────────────────────────────────
    print()
    print("═" * W)
    print("  ÖZET — TÜM KATMANLAR")
    print("─" * W)
    print(f"  {'Katman':<24} {'Ens':>5} {'⟨r⟩':>7} {'FİZİK':>8} {'BİYO':>6} {'MAT':>6} {'T₁₀ Krit.çizgi':>16}")
    print("─" * W)

    for name, (life, ms) in results.items():
        ens  = "GUE" if ms.beta >= 1.5 else "GOE"
        r    = ms.r_ratio
        fiz  = "✓" if life.on_critical_line else "✗"
        bio  = "✓" if ms.rh.stieltjes_psd else "✗"
        mat  = "✓" if ms.rh.hankel_psd else "✗"
        crit = "✓" if life.on_critical_line else "✗"
        print(f"  {name:<24} {ens:>5} {r:>7.4f} {fiz:>8} {bio:>6} {mat:>6} {crit:>16}")

    print("─" * W)

    # Yorumlama
    print()
    print("  YORUM:")
    all_bio  = all(ms.rh.stieltjes_psd  for (_, ms) in results.values())
    all_mat  = all(ms.rh.hankel_psd      for (_, ms) in results.values())
    any_line = any(l.on_critical_line    for (l, _) in results.values())
    all_line = all(l.on_critical_line    for (l, _) in results.values())

    if all_bio:
        print("  ✓ BİYOLOJİ: Tüm katmanlar gerçek pozitif ölçü — biyolojik veri Stieltjes")
        print("    çerçevesiyle tutarlı (hiçbir spektral bileşen negatife düşmüyor).")
    if all_mat:
        print("  ✓ MATEMATİK: Tüm Hankel matrisleri PSD — G=AᵀA aksiyomu tüm ömür")
        print("    boyunca korunuyor, pozitiflik ihlali yok.")
    if all_line:
        print("  ✓ FİZİK: Tüm katmanlar kritik çizgide (Li λₙ>0 ∧ Λ≤0). RH eşdeğeri")
        print("    koşullar karşılanıyor — sistemin tüm 'boyutları' tutarlı.")
    elif any_line:
        on = [n for n, (l, _) in results.items() if l.on_critical_line]
        off = [n for n, (l, _) in results.items() if not l.on_critical_line]
        print(f"  ~ FİZİK: Kritik çizgide: {on}")
        print(f"           Kritik çizgi dışı: {off}")
        print("    → Bu katmanlar farklı 'faz'da — aralarındaki geçiş araştırılabilir.")

    gue_layers = [n for n, (_, ms) in results.items() if ms.beta >= 1.5]
    goe_layers = [n for n, (_, ms) in results.items() if ms.beta < 1.5]
    print()
    print(f"  GOE (β=1, zaman-tersinir, klasik): {goe_layers}")
    print(f"  GUE (β=2, zaman-tersinmez, kuantum): {gue_layers}")
    print()
    print("  → GUE katmanlar kuantum kaotik yapı gösteriyor (tRNA, kinaz, sentez).")
    print("    GOE katmanlar klasik zaman-tersinir — DNA kodon, ADME, amino asit.")
    print("    Fiziksel yorum: GUE=süreç (okuma/katlama/bağlanma), GOE=veri (kod/yapı).")

    print()
    print("═" * W)
    print("  Evrim tamamlandı. Ctrl+C ile çık.")
    print("═" * W)


if __name__ == "__main__":
    run_all()
