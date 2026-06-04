#!/usr/bin/env python3
"""Proof-chain artifact audit for Tantrium.

This tool is not a theorem prover. It is a repository integrity check: every
major theorem file in the RH chain must exist and contain the structural markers
that the final manuscript depends on.
"""

from __future__ import annotations

from pathlib import Path
import sys

REQUIRED = {
    "theorems/D_POSITIVITY_THEOREM.md": [
        "D(m,ell,a) >= 0",
        "canonical refinement",
        "fiber-cancellation",
        "Uniform Lift",
        "D-positivity",
    ],
    "docs/DYADIC_TRANSPORT_THEOREM.md": [
        "iota",
        "kappa_s",
        "C_cell",
        "global D-positivity",
    ],
    "theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md": [
        "C_cell(s) > 0",
        "kappa_s",
        "strict surplus",
        "iota(D) subset S",
    ],
    "theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md": [
        "M_{a,b}(t)",
        "s_{a+b}(t)",
        "path--atom bijection",
        "Lindstrom-Gessel-Viennot",
        "tau_{d,j}(t)",
    ],
    "theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md": [
        "subdiscriminant",
        "Sturm",
        "Jensen",
        "Laguerre-Polya",
        "Riemann Hypothesis",
        "tau_j = Disc_j",
    ],
    "docs/TANTRIUM_FINAL_MANUSCRIPT.md": [
        "D(m,ell,a) >= 0",
        "Hankel/tau",
        "Sturm",
        "Jensen",
        "Riemann Hypothesis",
    ],
    "paper/TANTRIUM_RH_MAIN_THEOREM.md": [
        "D-positivity",
        "AG/LGV transfer identity",
        "Tau-Sturm subresultant identity",
        "Jensen hyperbolicity",
        "Riemann Hypothesis",
    ],
    "tools/ag_lgv_transfer_checker.py": [
        "AG/LGV TRANSFER CHECK",
        "M_{a,b}=s_{a+b}",
    ],
    "tools/tau_sturm_identity_checker.py": [
        "TAU/STURM IDENTITY CHECK",
        "subdiscriminant",
    ],
}


def main() -> int:
    root = Path.cwd()
    failures: list[str] = []
    for rel, markers in REQUIRED.items():
        path = root / rel
        if not path.exists():
            failures.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"missing marker in {rel}: {marker}")

    print("TANTRIUM PROOF CHAIN AUDIT")
    print(f"checked_files={len(REQUIRED)}")
    if failures:
        print(f"FAIL failures={len(failures)}")
        for f in failures[:30]:
            print("-", f)
        return 1
    print("PASS required theorem artifacts and executable audit markers found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
