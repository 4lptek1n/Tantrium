#!/usr/bin/env python3
"""Run Research OS v2 proof strategy attempts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.proof_strategies import run_strategy_matrix


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium proof strategy engine v2")
    parser.add_argument("--campaign", default="subresultant_recurrence")
    args = parser.parse_args()
    result = run_strategy_matrix(args.campaign)
    print("TANTRIUM PROOF STRATEGY ENGINE V2")
    print(f"CAMPAIGN: {args.campaign}")
    print(f"CANDIDATES: {result['candidate_count']}")
    print("RESULT: PROOF_ATTEMPTS_RECORDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
