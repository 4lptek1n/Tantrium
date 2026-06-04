#!/usr/bin/env python3
"""q=6 obstruction analyzer for Tantrium Proof Foundry.

The scan-all report (ell=1..5, model=qdiff) shows a persistent obstruction
line at q=6 across every ell >= 3:

  ell=3 q=6  FAIL  (row_156, row_159, row_161 uncovered)
  ell=4 q=6  FAIL  (row_56, row_268, row_269 uncovered)
  ell=5 q=6  FAIL  (row_401, row_402, row_699 uncovered)

This script:
  1. Loads the mixed-depth kernel for each ell=3,4,5.
  2. Extracts the q=6 source+deficit picture.
  3. Runs five models: qdiff, qgap, q6_low_family, diagonal_residue, unit.
  4. Reports: which models cover which deficits, first uncovered cell,
     total uncovered mass, fractional breakdown.
  5. Prints a recommendation for the auto-dispatch routing.

Usage:
    python tools/q6_obstruction_analyzer.py [--max-ell N] [--q-mode MODE]
"""
from __future__ import annotations

import argparse
import csv
import sys
from fractions import Fraction
from pathlib import Path

# tools/tantrium.py shadows the `tantrium` package when `tools/` is on
# sys.path. Remove any tools/ entries before inserting the repo root so
# that `import tantrium` resolves to the tantrium/ package, not the CLI.
_repo_root = str(Path(__file__).resolve().parents[1])
sys.path = [_repo_root] + [p for p in sys.path
                            if not p.endswith("/tools") and p != _repo_root]

from tantrium.certificates.certificate import Cell
from tantrium.transport.dyadic_flow import cells_from_rows
from tantrium.transport.model_dispatch import (
    auto_select_model,
    edge_allowed_extended,
    half_power_extended,
    solve_auto_greedy,
)


# ------------------------------------------------------------------
# q=6 load helper
# ------------------------------------------------------------------

def q_value(qd: int, p: int, mode: str) -> int:
    if mode == "two_qd":      return 2 * qd
    if mode == "qd":          return qd
    if mode == "qd_plus_p":   return qd + p
    if mode == "two_qd_plus_p": return 2 * (qd + p)
    raise ValueError(mode)


def load_q6_cells(path: Path, q_mode: str, q_target: int = 6,
                  source_policy: str = "q_ge_target"):
    sources, deficits = [], []
    with path.open(newline="") as f:
        for idx, row in enumerate(csv.DictReader(f), start=1):
            qd   = int(row.get("qd_power", 0))
            p    = int(row.get("qdm1_power", 0))
            y    = int(row.get("Y_power", 0))
            diff = y - p
            q    = q_value(qd, p, q_mode)
            coeff = Fraction(row.get("coefficient", "0"))
            cid   = f"row_{idx}"
            if coeff < 0 and q == q_target:
                deficits.append(
                    Cell.make(cid, -coeff, q=q, qd=qd, p=p, Y=y, diff=diff)
                )
            elif coeff > 0:
                ok = (
                    source_policy == "all"
                    or (source_policy == "target_only" and q == q_target)
                    or (source_policy == "q_ge_target" and q >= q_target)
                    or (source_policy == "q_gt_target" and q > q_target)
                )
                if ok:
                    sources.append(
                        Cell.make(cid, coeff, q=q, qd=qd, p=p, Y=y, diff=diff)
                    )
    return sources, deficits


# ------------------------------------------------------------------
# Run one model and return coverage stats
# ------------------------------------------------------------------

def run_model(sources, deficits, ell, q_target, model):
    """Return (status, uncovered_dict, total_uncovered_mass, cert)."""
    from fractions import Fraction
    cert = solve_auto_greedy(
        sources, deficits,
        ell=ell, q_target=q_target,
        theorem_id=f"q6_analysis_ell{ell}",
        kernel_id=f"ell{ell}_mixed_depth",
        model=model,
    )
    uncovered = cert.uncovered_deficits()
    total_mass = sum(uncovered.values(), Fraction(0))
    return cert.status, uncovered, total_mass, cert


# ------------------------------------------------------------------
# Print coverage table
# ------------------------------------------------------------------

MODELS = ["qdiff", "qgap", "q6_low_family", "diagonal_residue", "unit"]


def analyze_ell_q6(ell: int, kernel_path: Path, q_mode: str, verbose: bool):
    sources, deficits = load_q6_cells(kernel_path, q_mode, q_target=6)

    if not deficits:
        print(f"  ell={ell}: NO q=6 deficit rows in kernel — nothing to analyze.")
        return

    total_deficit_mass = sum(c.mass for c in deficits)
    print(f"\n{'='*70}")
    print(f"  ell={ell}  q=6  |  "
          f"sources={len(sources)}  deficits={len(deficits)}  "
          f"total_deficit_mass={total_deficit_mass}")

    # Source q-distribution
    q_dist: dict[int, int] = {}
    for s in sources:
        q_dist[s.coords.get("q", 0)] = q_dist.get(s.coords.get("q", 0), 0) + 1
    print(f"  source q-distribution: "
          + "  ".join(f"q={q}:{n}" for q, n in sorted(q_dist.items())))

    # Deficit coords
    if verbose:
        print(f"  deficit cells:")
        for d in sorted(deficits, key=lambda c: -c.mass):
            print(f"    {d.cell_id:>10}  mass={d.mass}  "
                  f"q={d.coords.get('q')}  qd={d.coords.get('qd')}  "
                  f"p={d.coords.get('p')}  Y={d.coords.get('Y')}  "
                  f"diff={d.coords.get('diff')}")

    print(f"\n  {'model':<22} {'status':>8}  {'uncovered':>10}  "
          f"{'frac_covered':>13}  notes")
    print("  " + "-" * 65)

    results = {}
    for model in MODELS:
        status, uncovered, total_unc, cert = run_model(
            sources, deficits, ell, 6, model
        )
        frac_covered = (
            float((total_deficit_mass - total_unc) / total_deficit_mass)
            if total_deficit_mass > 0 else 1.0
        )
        is_auto = (model == auto_select_model(ell, 6))
        note = " ← AUTO" if is_auto else ""
        if status == "failed" and uncovered:
            first = min(uncovered.keys(),
                        key=lambda k: (-uncovered[k], k))
            note += f"  first_gap={first}:{uncovered[first]}"
        print(f"  {model:<22} {status:>8}  {str(total_unc):>10}  "
              f"{frac_covered:>13.4f}{note}")
        results[model] = (status, uncovered, total_unc)

    # Recommendation
    passing = [m for m in MODELS if results[m][0] == "verified_exact"]
    auto_m  = auto_select_model(ell, 6)
    auto_ok = results[auto_m][0] == "verified_exact"
    print(f"\n  Passing models: {passing or ['none']}")
    print(f"  Auto model ({auto_m}): {'✓ PASS' if auto_ok else '✗ FAIL'}")

    if not passing:
        # Find best partial
        best = min(MODELS, key=lambda m: results[m][2])
        print(f"  No model fully covers q=6 at ell={ell}.")
        print(f"  Best partial: {best} "
              f"(uncovered mass = {results[best][2]})")
        print(f"  → q=6 at ell={ell} requires a NEW model or kernel extension.")
    elif auto_m not in passing:
        alt = passing[0]
        print(f"  → Update auto_select_model: ell={ell}, q=6 → '{alt}'")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Analyze q=6 obstruction across ell layers"
    )
    ap.add_argument("--max-ell", type=int, default=5)
    ap.add_argument("--q-mode", default="two_qd",
                    choices=["two_qd", "qd", "qd_plus_p", "two_qd_plus_p"])
    ap.add_argument("--kernel-dir", default="results/engine")
    ap.add_argument("--verbose", action="store_true",
                    help="Show per-cell deficit breakdown")
    args = ap.parse_args()

    import os; os.chdir(Path(__file__).resolve().parents[1])

    print("=" * 70)
    print("  TANTRIUM — q=6 OBSTRUCTION ANALYZER")
    print(f"  max_ell={args.max_ell}  q_mode={args.q_mode}")
    print("=" * 70)
    print("\n  Auto-dispatch routing table (from model_dispatch.py):")
    print(f"    ell=1        → split_pair")
    print(f"    ell=2        → diagonal_residue")
    print(f"    ell>=3, q=6  → q6_low_family")
    print(f"    ell>=3, q≠6  → qdiff")

    for ell in range(3, args.max_ell + 1):
        kpath = Path(args.kernel_dir) / f"ell{ell}_mixed_depth_kernel.csv"
        if not kpath.exists():
            print(f"\n  ell={ell}: kernel not found at {kpath} — skipping.")
            continue
        analyze_ell_q6(ell, kpath, args.q_mode, args.verbose)

    print(f"\n{'='*70}")
    print("  SUMMARY")
    print("=" * 70)
    print("""
  If q6_low_family passes at all ell>=3 with q=6:
    → model=auto is ready; integrate via tantrium.py --model auto

  If q6_low_family still fails:
    → The q=6 obstruction is a deeper structural gap.
    → Next steps: kernel extension (add more source rows at low q)
      or a targeted 'q6_low_family' model with different half_power.

  To integrate model=auto into the CLI:
    1. Add 'auto' to --model choices in tantrium.py
    2. In certify_one, when model=='auto', import and call
       tantrium.transport.model_dispatch.solve_auto_greedy instead of
       dyadic_flow.solve_greedy.
""")


if __name__ == "__main__":
    main()
