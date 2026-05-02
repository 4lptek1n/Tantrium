#!/usr/bin/env python3
"""Verify recurrence candidates on finite evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.recurrence.recurrence_miner import candidate_recurrences
from tantrium.research_os.recurrence.recurrence_verifier import verify_candidates


def main() -> int:
    out_dir = REPO_ROOT / "results" / "research_os" / "campaigns" / "subresultant_recurrence"
    qjr = json.loads((out_dir / "qjr_tables.json").read_text(encoding="utf-8"))
    verification = verify_candidates(candidate_recurrences(), qjr)
    (out_dir / "finite_verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TANTRIUM RECURRENCE VERIFIER")
    print(f"FINITE_CHECKS: {verification['all_finite_checks_passed']}")
    print("RESULT: VERIFIED_FINITE" if verification["all_finite_checks_passed"] else "RESULT: FAILED")
    return 0 if verification["all_finite_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
