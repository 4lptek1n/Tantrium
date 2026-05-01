#!/usr/bin/env python3
"""Proof-chain artifact audit for Tantrium."""

from __future__ import annotations

from pathlib import Path
import sys

REQUIRED = {
    "theorems/D_POSITIVITY_THEOREM.md": [
        "D(m,ell,a) >= 0",
        "canonical refinement",
        "fiber-cancellation",
        "Uniform Lift",
    ],
    "docs/DYADIC_TRANSPORT_THEOREM.md": [
        "iota",
        "kappa_s",
        "global D-positivity",
    ],
    "theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md": [
        "C_cell(s) > 0",
        "kappa_s",
        "strict surplus",
    ],
    "theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md": [
        "M_{a,b}(t)",
        "s_{a+b}(t)",
        "Lindstrom-Gessel-Viennot",
        "tau_{d,j}(t)",
    ],
    "theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md": [
        "subdiscriminant",
        "Sturm",
        "Jensen",
        "Laguerre-Polya",
        "Riemann Hypothesis",
    ],
    "docs/TANTRIUM_FINAL_MANUSCRIPT.md": [
        "D(m,ell,a) >= 0",
        "Hankel/tau",
        "Sturm",
        "Jensen",
        "Riemann Hypothesis",
    ],
}


def main() -> int:
    root = Path.cwd()
    failures = []
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
    if failures:
        print(f"FAIL failures={len(failures)}")
        for f in failures[:20]:
            print("-", f)
        return 1
    print("PASS required theorem artifacts and markers found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
